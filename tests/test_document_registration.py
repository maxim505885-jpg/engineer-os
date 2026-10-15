import unittest

from engineering.document_intelligence.document_registration import (
    SourceDocumentIdentity,
    assert_document_identity,
)


class DocumentRegistrationTests(unittest.TestCase):
    def test_matching_registered_checksum_passes(self):
        identity = SourceDocumentIdentity("p", "d", "a" * 64)
        assert_document_identity("a" * 64, identity)

    def test_different_version_is_blocked(self):
        identity = SourceDocumentIdentity("p", "d", "a" * 64)
        with self.assertRaises(ValueError):
            assert_document_identity("b" * 64, identity)

    def test_malformed_checksum_is_rejected(self):
        with self.assertRaises(ValueError):
            SourceDocumentIdentity("p", "d", "not-a-hash")


if __name__ == "__main__":
    unittest.main()
