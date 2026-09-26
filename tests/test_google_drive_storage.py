import io
import json
import tempfile
import unittest
from pathlib import Path

from engineering.storage.google_drive import (
    GoogleDriveClient,
    GoogleDriveError,
    GoogleDriveFile,
    GoogleDriveOAuth,
    GoogleDriveTokenProvider,
)


class _Response:
    def __init__(self, body):
        self._stream = io.BytesIO(body)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size=-1):
        return self._stream.read(size)


class _Token:
    def access_token(self):
        return "token"


class GoogleDriveStorageTests(unittest.TestCase):
    def test_refresh_token_exchange(self):
        seen = []
        def opener(req, timeout):
            seen.append((req, timeout))
            return _Response(json.dumps({"access_token": "fresh"}).encode())
        provider = GoogleDriveTokenProvider(
            GoogleDriveOAuth("client", "secret", "refresh"), opener
        )
        self.assertEqual(provider.access_token(), "fresh")
        self.assertEqual(seen[0][0].full_url, "https://oauth2.googleapis.com/token")
        self.assertNotIn("refresh", seen[0][0].headers)

    def test_refresh_token_exchange_without_client_secret(self):
        seen = []
        def opener(req, timeout):
            seen.append(req.data.decode("ascii"))
            return _Response(json.dumps({"access_token": "fresh"}).encode())
        provider = GoogleDriveTokenProvider(
            GoogleDriveOAuth("client", "", "refresh"), opener
        )
        self.assertEqual(provider.access_token(), "fresh")
        self.assertNotIn("client_secret", seen[0])

    def test_metadata_and_download_are_source_hashed(self):
        payload = b"%PDF-1.7 real report"
        metadata = {
            "id": "drive-id",
            "name": "report.pdf",
            "mimeType": "application/pdf",
            "size": str(len(payload)),
            "md5Checksum": "md5",
            "modifiedTime": "2026-09-26T00:00:00Z",
            "parents": ["folder"],
            "webViewLink": "https://drive.google.com/file/d/drive-id/view",
            "capabilities": {"canDownload": True},
            "trashed": False,
        }
        def opener(req, timeout):
            if "alt=media" in req.full_url:
                return _Response(payload)
            return _Response(json.dumps(metadata).encode())

        client = GoogleDriveClient(_Token(), opener)
        with tempfile.TemporaryDirectory() as folder:
            out = client.download("drive-id", str(Path(folder) / "report.pdf"))
            self.assertEqual(out.bytes_written, len(payload))
            self.assertEqual(Path(out.local_path).read_bytes(), payload)
            self.assertEqual(len(out.source_sha256), 64)
            self.assertEqual(out.metadata.file_id, "drive-id")

    def test_download_permission_is_fail_closed(self):
        client = GoogleDriveClient(_Token(), lambda req, timeout: _Response(json.dumps({
            "id": "x", "name": "x.pdf", "mimeType": "application/pdf",
            "size": "10", "capabilities": {"canDownload": False}, "trashed": False
        }).encode()))
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(GoogleDriveError):
                client.download("x", str(Path(folder) / "x.pdf"))

    def test_oversize_metadata_blocks_before_media_download(self):
        calls = []
        def opener(req, timeout):
            calls.append(req.full_url)
            return _Response(json.dumps({
                "id": "x", "name": "x.pdf", "mimeType": "application/pdf",
                "size": "999", "capabilities": {"canDownload": True}, "trashed": False
            }).encode())
        client = GoogleDriveClient(_Token(), opener)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(GoogleDriveError):
                client.download("x", str(Path(folder) / "x.pdf"), max_bytes=100)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
