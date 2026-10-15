"""Explicit offline Gotenberg pilot; not an application acceptance issuer."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.compare_document_visuals import read_regular, new_directory, sha


def runtime_command(runtime):
    # Explicit local transport ignores a user's remote Docker context/DOCKER_HOST.
    if Path(runtime).stem.lower() == 'podman':
        if os.name == 'nt':
            raise ValueError('Windows Podman remote transport is not qualified by this pilot')
        return [str(runtime), '--remote=false']
    endpoint = 'npipe:////./pipe/docker_engine' if os.name == 'nt' else 'unix:///var/run/docker.sock'
    return [str(runtime), '--host', endpoint]


def container_command(runtime, image, name):
    if not isinstance(image, str) or not re.fullmatch(r'gotenberg/gotenberg@sha256:[0-9a-f]{64}', image):
        raise ValueError('Use a locally available official image pinned by SHA256 digest')
    if not re.fullmatch(r'engineer-office-[a-z0-9-]{1,64}', name):
        raise ValueError('Invalid private container name')
    return runtime_command(runtime) + ['create', '--pull=never', '--name', name, '--network=none',
        '--read-only', '--user=1001:1001', '--env=HOME=/tmp', '--workdir=/tmp', '--cap-drop=ALL', '--security-opt=no-new-privileges:true',
        '--memory=3g', '--memory-swap=3g', '--cpus=2', '--pids-limit=256',
        '--tmpfs=/tmp:rw,noexec,nosuid,size=2g', image, 'gotenberg',
        '--api-bind-ip=127.0.0.1', '--api-timeout=180s', '--api-body-limit=257MB',
        '--api-disable-download-from=true', '--chromium-disable-routes=true',
        '--webhook-disable=true', '--libreoffice-deny-list=.*']


def render(source, output, *, image, runtime='docker'):
    runtime = shutil.which(runtime)
    if not runtime:
        raise ValueError('CONTAINER_RUNTIME_UNAVAILABLE: Docker/Podman is required')
    runtime = str(Path(runtime).resolve())
    base = runtime_command(runtime)
    clean_env = dict(os.environ)
    for key in ('DOCKER_CONTEXT', 'DOCKER_HOST', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH', 'CONTAINER_HOST', 'CONTAINER_CONNECTION'):
        clean_env.pop(key, None)
    name = 'engineer-office-'+uuid.uuid4().hex
    command = container_command(runtime, image, name)
    source, data = read_regular(source)
    if source.suffix.lower() != '.docx' or not data.startswith(b'PK'):
        raise ValueError('This pilot accepts DOCX only')
    output = new_directory(output)
    report = dict(schema='ENGINEER_OS_OFFLINE_OFFICE_PILOT_V1', status='BLOCK',
        source_sha256=sha(data), image=image, runtime_sha256=sha(read_regular(runtime)[1]),
        adapter_sha256=sha(Path(__file__).read_bytes()), network_mode='none',
        host_mounts=[], published_ports=[], isolation_qualified=False,
        document_completeness='NOT_QUALIFIED', acceptance_granted=False,
        pdf_sha256=None, cleanup_completed=False, reasons=[])
    created = False
    def run(args, *, timeout=30, **kwargs):
        return subprocess.run(args, timeout=timeout, check=True, env=clean_env, **kwargs)
    try:
        with (output/'engine.log').open('xb') as log:
            try:
                # No implicit image download, host bind mount, or published socket.
                created = True  # cleanup even if create times out after daemon accepted it
                run(command, stdout=log, stderr=log)
                run(base + ['start', name], stdout=log, stderr=log)
                for attempt in range(15):
                    probe = subprocess.run(base + ['exec', name, 'curl', '--fail', '--silent',
                        '--max-time', '2', 'http://127.0.0.1:3000/health'],
                        timeout=5, stdout=log, stderr=log, check=False, env=clean_env)
                    if probe.returncode == 0:
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError('CONTAINER_HEALTH_UNAVAILABLE')
                boundary = 'engineer'+uuid.uuid4().hex
                body = ('--'+boundary+'\r\nContent-Disposition: form-data; name="files"; '
                    'filename="source.docx"\r\nContent-Type: application/vnd.openxmlformats-officedocument.'
                    'wordprocessingml.document\r\n\r\n').encode()+data+('\r\n--'+boundary+'--\r\n').encode()
                target = output/'derived.pdf'
                with target.open('xb') as pdf:
                    run(base + ['exec', '-i', name, 'curl', '--fail', '--silent', '--show-error',
                        '--max-time', '180', '--max-filesize', '268435456', '--request', 'POST',
                        '--header', 'Content-Type: multipart/form-data; boundary='+boundary,
                        '--data-binary', '@-', 'http://127.0.0.1:3000/forms/libreoffice/convert'],
                        input=body, stdout=pdf, stderr=log, timeout=195)
                report['pdf_sha256'] = sha(read_regular(target, pdf=True)[1])
                report['status'] = 'DERIVED_UNVERIFIED'
            finally:
                if created:
                    cleanup = subprocess.run(base + ['rm', '--force', name], timeout=30,
                        stdout=log, stderr=log, check=False, env=clean_env)
                    report['cleanup_completed'] = cleanup.returncode == 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report['reasons'].append(type(error).__name__)
        report['status'] = 'BLOCK'
    try:
        unchanged = sha(read_regular(source)[1]) == sha(data)
    except (OSError, ValueError):
        unchanged = False
    if not unchanged:
        report['status'] = 'BLOCK'
        report['reasons'].append('SOURCE_CHANGED')
    if not report['cleanup_completed']:
        report['status'] = 'BLOCK'
        report['reasons'].append('CONTAINER_CLEANUP_NOT_CONFIRMED')
    with (output/'manifest.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--runtime', default='docker', choices=['docker', 'podman'])
    args = parser.parse_args()
    try:
        report = render(args.source, args.output, image=args.image, runtime=args.runtime)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error)+'\n')
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report['status'] == 'DERIVED_UNVERIFIED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
