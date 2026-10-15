"""Bind a Google Drive source file to a registered ENGINEER OS document identity."""

from __future__ import annotations

from pathlib import Path

from engineering.document_intelligence.document_registration import (
    SourceDocumentIdentity,
    assert_document_identity,
)

from .google_drive import DownloadedDriveFile, GoogleDriveClient


def materialize_registered_drive_document(
    client: GoogleDriveClient,
    *,
    drive_file_id: str,
    identity: SourceDocumentIdentity,
    destination: str,
    max_bytes: int = 500 * 1024 * 1024,
) -> DownloadedDriveFile:
    downloaded = client.download(drive_file_id, destination, max_bytes=max_bytes)
    try:
        assert_document_identity(downloaded.source_sha256, identity)
    except Exception:
        Path(downloaded.local_path).unlink(missing_ok=True)
        raise
    return downloaded
