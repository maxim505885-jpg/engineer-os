"""External storage adapters for ENGINEER OS."""

from .drive_document_source import materialize_registered_drive_document
from .google_drive import (
    DownloadedDriveFile,
    GoogleDriveClient,
    GoogleDriveError,
    GoogleDriveFile,
    GoogleDriveOAuth,
    GoogleDriveTokenProvider,
    production_google_drive_client,
)

__all__ = [
    "DownloadedDriveFile",
    "GoogleDriveClient",
    "GoogleDriveError",
    "GoogleDriveFile",
    "GoogleDriveOAuth",
    "GoogleDriveTokenProvider",
    "production_google_drive_client",
    "materialize_registered_drive_document",
]
