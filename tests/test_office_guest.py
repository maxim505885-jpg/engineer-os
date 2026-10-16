"""Validate guest-worker input and invocation contracts without executing Office."""
import contextlib
import io
from unittest.mock import patch
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from runtime.office_guest import parse_request, validate_source, office_command, registry_xml, GuestInputError

class OfficeGuestTests(unittest.TestCase):
    def request(self, **changes):
        value=dict(schema=1,source_sha256="a"*64,suffix=".docx")
        value.update(changes)
        return json.dumps(value).encode()

    def test_input_read_failure_records_last_reached_phase(self):
        from runtime.office_guest import main
        phases=[]
        with patch('runtime.office_guest.phase',side_effect=phases.append),patch('runtime.office_guest._bounded_read',side_effect=[self.request(),GuestInputError('owned read failure')]),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(),1)
        self.assertEqual(phases,['REQUEST_READ_BEGIN','REQUEST_READ_COMPLETE','INPUT_READ_BEGIN'])
    def test_only_exact_request_contract(self):
        self.assertEqual(parse_request(self.request())["suffix"], ".docx")
        for value in [self.request(extra=True), self.request(schema=True),self.request(suffix=".exe"),self.request(suffix="../source.docx"),self.request(source_sha256="A"*64),b'{"schema":1,"schema":1}',b"x"*4097]:
            with self.subTest(value=value[:100]),self.assertRaises(GuestInputError):parse_request(value)

    def test_supported_source_signatures_and_identity(self):
        for suffix,data in [(".doc",bytes.fromhex("d0cf11e0a1b11ae1")+b"owned"),(".docx",b"PK\x03\x04owned"),(".rtf",b"{\\rtf1 owned}")]:
            request=parse_request(self.request(suffix=suffix,source_sha256=hashlib.sha256(data).hexdigest()))
            validate_source(data,request)
            with self.assertRaises(GuestInputError):validate_source(data+b"changed",request)

    def test_empty_and_wrong_format_rejected(self):
        for data in [b"",b"executable",b"{\\rtf1}"]:
            request=parse_request(self.request(source_sha256=hashlib.sha256(data).hexdigest()))
            with self.assertRaises(GuestInputError):validate_source(data,request)

    def test_office_command_and_profile_are_passive(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            command=office_command(root, ".docx")
            self.assertEqual(command[0],"/usr/bin/libreoffice")
            self.assertIn("--headless",command)
            self.assertIn("pdf:writer_pdf_Export",command)
            self.assertEqual(command[-1],str(root/"source.docx"))
            self.assertNotIn("--accept", " ".join(command))
        self.assertIn("MacroSecurityLevel",registry_xml())
        self.assertIn("<value>3</value>",registry_xml())
        self.assertIn('oor:name="Link"',registry_xml())

if __name__=="__main__":unittest.main()
