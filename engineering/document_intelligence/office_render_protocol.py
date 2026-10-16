"""Bounded decoding of untrusted renderer output; no isolation or acceptance claim.

Callers must separately verify worker exit, isolation, runtime identity and input
preservation. A PDF signature is not structural or engineering validation.
"""
import base64
import binascii
import hashlib
import json
import re

MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_SERIAL_BYTES = 48 * 1024 * 1024
_HASH = re.compile(r"[0-9a-f]{64}")

class RenderProtocolError(ValueError):
    """Renderer output cannot be bound to the requested source safely."""

def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RenderProtocolError("Duplicate renderer JSON key")
        result[key] = value
    return result

def decode_render_result(payload, expected_source_sha256, *, max_pdf_bytes=MAX_PDF_BYTES):
    """Return bounded PDF bytes and source lineage; reject ambiguous frames."""
    if not isinstance(expected_source_sha256, str) or not _HASH.fullmatch(expected_source_sha256):
        raise RenderProtocolError("Invalid expected source identity")
    if type(max_pdf_bytes) is not int or not 0 < max_pdf_bytes <= MAX_PDF_BYTES:
        raise RenderProtocolError("Invalid output size limit")
    if not isinstance(payload, bytes) or len(payload) > MAX_SERIAL_BYTES:
        raise RenderProtocolError("Renderer stream size/type limit")
    # The wire format has six lines and one unwrapped base64 body. Count
    # separators before decoding/splitting, so malformed floods cannot allocate
    # millions of Python line objects within the byte budget.
    if payload.count(b"\n") > 6 or payload.count(b"\r") > 6:
        raise RenderProtocolError("Renderer frame line limit")
    header = ("ENGINEER_INPUT_SHA256 " + expected_source_sha256).encode("ascii")
    if not payload.startswith((header + b"\n", header + b"\r\n")):
        raise RenderProtocolError("Source identity mismatch or missing frame")
    try:
        lines = payload.decode("ascii").split("\n")
        if lines[-1] == "":
            lines.pop()
        lines = [line.removesuffix("\r") for line in lines]
    except UnicodeError as exc:
        raise RenderProtocolError("Invalid renderer stream encoding") from exc
    if len(lines) != 6 or lines[0] != "ENGINEER_INPUT_SHA256 " + expected_source_sha256:
        raise RenderProtocolError("Source identity mismatch or missing frame")
    if not lines[1].startswith("ENGINEER_OFFICE_RESULT ") or len(lines[1]) > 16384:
        raise RenderProtocolError("Invalid renderer result frame")
    try:
        result = json.loads(lines[1][len("ENGINEER_OFFICE_RESULT "):], object_pairs_hook=_unique_object)
    except (ValueError, RecursionError) as exc:
        raise RenderProtocolError("Invalid renderer result JSON") from exc
    if not isinstance(result, dict) or type(result.get("code")) is not int or result["code"] != 0:
        raise RenderProtocolError("Renderer did not report success")
    prefix = "ENGINEER_PDF_SHA256 "
    if not lines[2].startswith(prefix) or not _HASH.fullmatch(lines[2][len(prefix):]):
        raise RenderProtocolError("Invalid output identity")
    expected_pdf = lines[2][len(prefix):]
    if lines[3] != "ENGINEER_PDF_BEGIN" or lines[-1] != "ENGINEER_PDF_END":
        raise RenderProtocolError("Invalid output framing")
    encoded = "".join(lines[4:-1])
    if len(encoded) > 4 * ((max_pdf_bytes + 2) // 3):
        raise RenderProtocolError("Derived output size limit")
    try:
        pdf = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise RenderProtocolError("Invalid output base64") from exc
    if not 0 < len(pdf) <= max_pdf_bytes:
        raise RenderProtocolError("Derived output size limit")
    actual_pdf = hashlib.sha256(pdf).hexdigest()
    if actual_pdf != expected_pdf:
        raise RenderProtocolError("Derived output identity mismatch")
    if not pdf.startswith(b"%PDF-") or not pdf.rstrip().endswith(b"%%EOF"):
        raise RenderProtocolError("Missing PDF signature/terminator")
    return pdf, dict(source_sha256=expected_source_sha256, derived_sha256=actual_pdf,
                     derived_bytes=len(pdf), scope="DERIVED_UNVERIFIED",
                     pdf_structure="NOT_VALIDATED", acceptance_granted=False)
