"""Linux guest Office worker; outer host containment is a separate requirement.

Never expose this as a host converter. The trusted guest controller starts it as
root, without a virtual NIC, and supplies only fw_cfg request/input files.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile

MAX_SOURCE = 64 * 1024 * 1024
MAX_PDF = 32 * 1024 * 1024
TIMEOUT = 150

class GuestInputError(ValueError):
    pass

def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise GuestInputError("Duplicate request key")
        result[key] = value
    return result

def parse_request(data):
    if not isinstance(data, bytes) or not 0 < len(data) <= 4096:
        raise GuestInputError("Request size/type limit")
    try: request = json.loads(data, object_pairs_hook=_unique)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise GuestInputError("Invalid request JSON") from exc
    if not isinstance(request, dict) or set(request) != {"schema", "source_sha256", "suffix"}:
        raise GuestInputError("Invalid request fields")
    if type(request["schema"]) is not int or request["schema"] != 1:
        raise GuestInputError("Invalid request schema")
    if request["suffix"] not in (".doc", ".docx", ".rtf"):
        raise GuestInputError("Unsupported source format")
    if not isinstance(request["source_sha256"], str) or not re.fullmatch("[0-9a-f]{64}", request["source_sha256"]):
        raise GuestInputError("Invalid source identity")
    return request

def validate_source(data, request):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_SOURCE:
        raise GuestInputError("Source size/type limit")
    if hashlib.sha256(data).hexdigest() != request["source_sha256"]:
        raise GuestInputError("Source identity mismatch")
    magic = {".doc": bytes.fromhex("d0cf11e0a1b11ae1"), ".docx": b"PK\x03\x04", ".rtf": b"{\\rtf"}
    if not data.startswith(magic[request["suffix"]]):
        raise GuestInputError("Source signature mismatch")

def registry_xml():
    return ('<oor:items xmlns:oor="http://openoffice.org/2001/registry">'
            '<item oor:path="/org.openoffice.Office.Common/Security/Scripting">'
            '<prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item>'
            '<item oor:path="/org.openoffice.Office.Writer/Content/Update">'
            '<prop oor:name="Link" oor:op="fuse"><value>2</value></prop></item></oor:items>')

def office_command(root, suffix):
    return ["/usr/bin/libreoffice", "-env:UserInstallation=" + (root / "profile").as_uri(),
            "--headless", "--nologo", "--nodefault", "--nofirststartwizard", "--norestore",
            "--convert-to", "pdf:writer_pdf_Export", "--outdir", str(root), str(root / ("source" + suffix))]

def _limits():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_AS, (3 * 1024**3, 3 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_PDF, MAX_PDF))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))

def _read_pdf(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_PDF:
            raise GuestInputError("Invalid derived file")
        data = stream.read(MAX_PDF + 1)
    if not 0 < len(data) <= MAX_PDF or not data.startswith(b"%PDF-") or not data.rstrip().endswith(b"%%EOF"):
        raise GuestInputError("Invalid derived PDF signature/size")
    return data

def render(data, request):
    if sys.platform != "linux" or os.geteuid() != 0:
        raise GuestInputError("Guest controller must run in dedicated Linux image")
    if sorted(p.name for p in Path("/sys/class/net").iterdir()) != ["lo"]:
        raise GuestInputError("Guest network interface present")
    validate_source(data, request)
    with tempfile.TemporaryDirectory(prefix="engineer-office-") as temp:
        root = Path(temp)
        os.chown(root, 65534, 65534)
        source = root / ("source" + request["suffix"])
        source.write_bytes(data)
        source.chmod(0o444)
        profile = root / "profile" / "user"
        profile.mkdir(parents=True)
        registry = profile / "registrymodifications.xcu"
        registry.write_text(registry_xml(), encoding="utf-8")
        for path in [profile.parent, profile, registry]: os.chown(path, 65534, 65534)
        env = dict(PATH="/usr/bin:/bin", HOME=str(root), LANG="C.UTF-8", TMPDIR=str(root))
        with (root / "worker.log").open("w+b") as log:
            child = subprocess.Popen(office_command(root, request["suffix"]), cwd=root, env=env,
                                     user=65534, group=65534, extra_groups=[], start_new_session=True,
                                     preexec_fn=_limits, stdin=subprocess.DEVNULL, stdout=log,
                                     stderr=subprocess.STDOUT, close_fds=True)
            try:
                code = child.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise GuestInputError("Office timeout") from None
            finally:
                # Includes lingering descendants even if the group leader exits.
                try: os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            log.seek(0)
            detail = log.read(2048).decode("utf-8", errors="replace")
        if code != 0: raise GuestInputError("Office conversion failed")
        return _read_pdf(root / "source.pdf"), detail

def _bounded_read(path, maximum):
    with path.open("rb") as stream: data = stream.read(maximum + 1)
    if len(data) > maximum: raise GuestInputError("Firmware input size limit")
    return data

def main():
    try:
        firmware = Path("/sys/firmware/qemu_fw_cfg/by_name/opt/eos")
        request = parse_request(_bounded_read(firmware / "request/raw", 4096))
        data = _bounded_read(firmware / "input/raw", MAX_SOURCE)
        pdf, log = render(data, request)
        print("ENGINEER_INPUT_SHA256 " + request["source_sha256"], flush=True)
        print("ENGINEER_OFFICE_RESULT " + json.dumps(dict(code=0, log=log), ensure_ascii=True), flush=True)
        print("ENGINEER_PDF_SHA256 " + hashlib.sha256(pdf).hexdigest(), flush=True)
        print("ENGINEER_PDF_BEGIN", flush=True)
        print(base64.b64encode(pdf).decode("ascii"), flush=True)
        print("ENGINEER_PDF_END", flush=True)
        return 0
    except Exception as exc:
        print("ENGINEER_OFFICE_RESULT " + json.dumps(dict(code=1, error=type(exc).__name__, detail=str(exc)[:1024]), ensure_ascii=True), flush=True)
        return 1

if __name__ == "__main__": raise SystemExit(main())
