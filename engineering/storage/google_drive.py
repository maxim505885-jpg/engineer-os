"""Read-only Google Drive storage adapter for ENGINEER OS.

Secrets are injected at runtime. Drive files remain external source artifacts;
downloading a file does not make its contents Evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from urllib import error, parse, request


class GoogleDriveError(RuntimeError):
    pass


@dataclass(frozen=True)
class GoogleDriveOAuth:
    client_id: str
    client_secret: str
    refresh_token: str

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.client_id, self.client_secret, self.refresh_token)):
            raise ValueError("Google Drive OAuth credentials are required")


@dataclass(frozen=True)
class GoogleDriveFile:
    file_id: str
    name: str
    mime_type: str
    size: int | None
    md5_checksum: str | None
    modified_time: str | None
    parents: tuple[str, ...]
    web_view_link: str | None
    can_download: bool
    trashed: bool


@dataclass(frozen=True)
class DownloadedDriveFile:
    metadata: GoogleDriveFile
    local_path: str
    source_sha256: str
    bytes_written: int


class GoogleDriveTokenProvider:
    def __init__(self, oauth: GoogleDriveOAuth, opener=None) -> None:
        self._oauth = oauth
        self._opener = opener or request.urlopen

    def access_token(self) -> str:
        payload = parse.urlencode({
            "client_id": self._oauth.client_id,
            "client_secret": self._oauth.client_secret,
            "refresh_token": self._oauth.refresh_token,
            "grant_type": "refresh_token",
        }).encode("ascii")
        req = request.Request(
            "https://oauth2.googleapis.com/token",
            data=payload,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with self._opener(req, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GoogleDriveError("Google OAuth token refresh failed") from exc
        token = body.get("access_token")
        if not isinstance(token, str) or not token.strip():
            raise GoogleDriveError("Google OAuth response did not contain an access token")
        return token


class GoogleDriveClient:
    _API = "https://www.googleapis.com/drive/v3/files/"

    def __init__(self, token_provider: GoogleDriveTokenProvider, opener=None) -> None:
        self._token_provider = token_provider
        self._opener = opener or request.urlopen

    def _headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer " + self._token_provider.access_token()}

    def metadata(self, file_id: str) -> GoogleDriveFile:
        if not file_id.strip():
            raise ValueError("Google Drive file_id is required")
        fields = "id,name,mimeType,size,md5Checksum,modifiedTime,parents,webViewLink,capabilities(canDownload),trashed"
        url = self._API + parse.quote(file_id, safe="") + "?" + parse.urlencode({"fields": fields})
        req = request.Request(url, method="GET", headers=self._headers())
        try:
            with self._opener(req, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GoogleDriveError("Google Drive metadata request failed") from exc
        try:
            size = int(body["size"]) if body.get("size") is not None else None
            return GoogleDriveFile(
                file_id=body["id"],
                name=body["name"],
                mime_type=body["mimeType"],
                size=size,
                md5_checksum=body.get("md5Checksum"),
                modified_time=body.get("modifiedTime"),
                parents=tuple(body.get("parents") or ()),
                web_view_link=body.get("webViewLink"),
                can_download=bool((body.get("capabilities") or {}).get("canDownload")),
                trashed=bool(body.get("trashed")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GoogleDriveError("Google Drive returned invalid file metadata") from exc

    def download(
        self,
        file_id: str,
        destination: str,
        *,
        max_bytes: int = 500 * 1024 * 1024,
    ) -> DownloadedDriveFile:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        metadata = self.metadata(file_id)
        if metadata.trashed:
            raise GoogleDriveError("Google Drive file is trashed")
        if not metadata.can_download:
            raise GoogleDriveError("Google Drive file is not downloadable")
        if metadata.size is not None and metadata.size > max_bytes:
            raise GoogleDriveError("Google Drive file exceeds configured size limit")

        url = self._API + parse.quote(file_id, safe="") + "?alt=media"
        req = request.Request(url, method="GET", headers=self._headers())
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256()
        written = 0
        try:
            with self._opener(req, timeout=300) as response, target.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        raise GoogleDriveError("Google Drive download exceeded configured size limit")
                    sha.update(chunk)
                    handle.write(chunk)
        except (error.HTTPError, error.URLError, TimeoutError, OSError) as exc:
            target.unlink(missing_ok=True)
            raise GoogleDriveError("Google Drive download failed") from exc
        except GoogleDriveError:
            target.unlink(missing_ok=True)
            raise

        if metadata.size is not None and written != metadata.size:
            target.unlink(missing_ok=True)
            raise GoogleDriveError("Google Drive download size mismatch")
        return DownloadedDriveFile(metadata, str(target), sha.hexdigest(), written)
