import tempfile
import unittest
from pathlib import Path

from engineering.document_intelligence.document_registration import SourceDocumentIdentity
from engineering.storage.drive_document_source import materialize_registered_drive_document
from engineering.storage.google_drive import DownloadedDriveFile, GoogleDriveFile


class _Client:
    def __init__(self, sha):
        self.sha = sha
    def download(self, file_id, destination, max_bytes):
        Path(destination).write_bytes(b"pdf")
        meta = GoogleDriveFile(file_id, "report.pdf", "application/pdf", 3, None, None, (), None, True, False)
        return DownloadedDriveFile(meta, destination, self.sha, 3)


class DriveDocumentSourceTests(unittest.TestCase):
    def setUp(self):
        self.identity = SourceDocumentIdentity(
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "a" * 64,
        )

    def test_registered_checksum_allows_materialization(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "report.pdf")
            result = materialize_registered_drive_document(
                _Client("a" * 64), drive_file_id="drive-id",
                identity=self.identity, destination=path,
            )
            self.assertEqual(result.source_sha256, "a" * 64)
            self.assertTrue(Path(path).exists())

    def test_checksum_mismatch_deletes_downloaded_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "report.pdf")
            with self.assertRaises(ValueError):
                materialize_registered_drive_document(
                    _Client("b" * 64), drive_file_id="drive-id",
                    identity=self.identity, destination=path,
                )
            self.assertFalse(Path(path).exists())


if __name__ == "__main__":
    unittest.main()
