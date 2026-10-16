"""Host validation of untrusted offline-renderer output, not document acceptance."""
import base64
import hashlib
import json
import unittest
import tracemalloc
from engineering.document_intelligence.office_render_protocol import decode_render_result, RenderProtocolError

SOURCE = "a" * 64
PDF = b"%PDF-1.7\nowned protocol fixture\n%%EOF\n"

def stream(pdf=PDF, source=SOURCE, code=0):
    return ("ENGINEER_INPUT_SHA256 " + source + "\nENGINEER_OFFICE_RESULT " + json.dumps({"code": code, "log": "owned fixture", "interfaces": ["lo"]}) + "\nENGINEER_PDF_SHA256 " + hashlib.sha256(pdf).hexdigest() + "\nENGINEER_PDF_BEGIN\n" + base64.b64encode(pdf).decode() + "\nENGINEER_PDF_END\n").encode()

class OfficeRenderProtocolTests(unittest.TestCase):
    def test_source_bound_output_remains_unverified(self):
        data, receipt = decode_render_result(stream(), SOURCE)
        self.assertEqual(data, PDF)
        self.assertEqual(receipt["source_sha256"], SOURCE)
        self.assertEqual(receipt["derived_sha256"], hashlib.sha256(PDF).hexdigest())
        self.assertEqual(receipt["scope"], "DERIVED_UNVERIFIED")
        self.assertFalse(receipt["acceptance_granted"])
        self.assertNotIn("network_denied", receipt)
        self.assertEqual(receipt["pdf_structure"], "NOT_VALIDATED")

    def test_wrong_source_rejected(self):
        with self.assertRaises(RenderProtocolError): decode_render_result(stream(source="b"*64), SOURCE)

    def test_invalid_expected_identity_rejected(self):
        for identity in ["", "A"*64, "x"*64, None]:
            with self.subTest(identity=identity), self.assertRaises(RenderProtocolError): decode_render_result(stream(), identity)

    def test_wrong_output_hash_rejected(self):
        bad = stream().replace(hashlib.sha256(PDF).hexdigest().encode(), b"b"*64)
        with self.assertRaises(RenderProtocolError): decode_render_result(bad, SOURCE)

    def test_duplicate_or_unframed_output_rejected(self):
        for bad in [stream()+stream(), b"noise\n"+stream(), stream()+b"trailing", stream().replace(b"ENGINEER_PDF_BEGIN", b"ENGINEER_PDF_BEGIN\nENGINEER_PDF_BEGIN")]:
            with self.subTest(size=len(bad)), self.assertRaises(RenderProtocolError): decode_render_result(bad, SOURCE)

    def test_failed_or_ambiguous_result_rejected(self):
        for bad in [stream(code=1), stream(code=True), stream().replace(b'"code": 0', b'"code": 1, "code": 0')]:
            with self.subTest(bad=bad[:120]), self.assertRaises(RenderProtocolError): decode_render_result(bad, SOURCE)

    def test_bad_base64_or_non_pdf_rejected(self):
        for bad in [stream().replace(base64.b64encode(PDF), b"invalid!"), stream(pdf=b"not pdf"), stream(pdf=b"%PDF-1.7 missing terminator")]:
            with self.assertRaises(RenderProtocolError): decode_render_result(bad, SOURCE)

    def test_newline_flood_rejected_without_memory_amplification(self):
        for separator in [b"\n", b"\r", b"\x0b", b"\x0c", b"\x1c", b"\x1d", b"\x1e"]:
            payload = separator * 1000000
            tracemalloc.start()
            try:
                with self.assertRaises(RenderProtocolError):
                    decode_render_result(payload, SOURCE)
                _, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            with self.subTest(separator=separator):
                self.assertLess(peak, 128 * 1024)

    def test_size_limit_applies_before_decode(self):
        with self.assertRaises(RenderProtocolError): decode_render_result(stream(), SOURCE, max_pdf_bytes=8)

if __name__ == "__main__": unittest.main()
