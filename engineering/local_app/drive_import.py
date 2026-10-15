"""Import read-only Drive originals into an isolated local conversation."""
import hashlib
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import parse_qs, urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler

from engineering.storage.google_drive import GoogleDriveClient, GoogleDriveOAuth, GoogleDriveTokenProvider
from .files import file_limit, preserve_file,SUPPORTED_SUFFIXES


class DriveImportError(RuntimeError):
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):return None


class BoundedJSON:
    def __init__(self, response):self.response=response
    def __enter__(self):return self
    def __exit__(self,*args):self.response.close()
    def read(self, size=-1):
        raw=self.response.read(1024*1024+1)
        if len(raw)>1024*1024:raise ValueError('Google JSON response exceeds limit')
        return raw


class GoogleOnlyTransport:
    def __init__(self):self.opener=build_opener(ProxyHandler({}),NoRedirect())
    def __call__(self, req, timeout):
        url=urlsplit(req.full_url)
        if (url.scheme!='https' or url.username is not None or url.password is not None
                or url.port not in (None,443) or url.fragment
                or not ((url.hostname=='oauth2.googleapis.com' and url.path=='/token')
                        or (url.hostname=='www.googleapis.com' and url.path.startswith('/drive/v3/files/')))):
            raise ValueError('Only fixed Google OAuth/Drive endpoints are allowed')
        response=self.opener.open(req,timeout=timeout)
        return response if parse_qs(url.query).get('alt')==['media'] else BoundedJSON(response)


def configured_client():
    client_id=os.environ.get('GOOGLE_DRIVE_CLIENT_ID','').strip()
    refresh=os.environ.get('GOOGLE_DRIVE_REFRESH_TOKEN','').strip()
    if not client_id or not refresh:return None
    oauth=GoogleDriveOAuth(client_id,os.environ.get('GOOGLE_DRIVE_CLIENT_SECRET',''),refresh)
    transport=GoogleOnlyTransport()
    return GoogleDriveClient(GoogleDriveTokenProvider(oauth,transport),transport)


def drive_file_id(value):
    if not isinstance(value,str) or not value.strip() or len(value)>2048:
        raise ValueError('Укажите ссылку или ID файла Google Drive')
    value=value.strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{6,200}',value):return value
    url=urlsplit(value)
    if (url.scheme!='https' or url.hostname!='drive.google.com' or url.username is not None
            or url.password is not None or url.port not in (None,443)):
        raise ValueError('Поддерживается только ссылка https://drive.google.com на файл')
    match=re.fullmatch(r'/file/d/([A-Za-z0-9_-]{6,200})(?:/view)?/?',url.path)
    if match:return match[1]
    ids=parse_qs(url.query).get('id',[]) if url.path=='/open' else []
    if len(ids)==1 and re.fullmatch(r'[A-Za-z0-9_-]{6,200}',ids[0]):return ids[0]
    raise ValueError('Нужна ссылка на оригинальный файл, не на папку или документ Google')


def validate_metadata(meta, requested_id):
    if meta.file_id!=requested_id:raise DriveImportError('Drive вернул другой ID файла')
    if meta.trashed is not False or meta.can_download is not True:
        raise DriveImportError('Файл удалён или скачивание недоступно')
    if (not isinstance(meta.name,str) or not meta.name.strip() or len(meta.name)>240
            or any(ord(c)<32 for c in meta.name)):
        raise DriveImportError('Некорректное имя оригинала Drive')
    suffix=Path(meta.name).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES or not isinstance(meta.mime_type,str) or meta.mime_type.startswith('application/vnd.google-apps.'):
        raise DriveImportError('Импортируются оригиналы PDF/TXT/MD/DOCX/XLSX/DOC/PNG/JPG/LIR/JSON/CSV; экспорт Google Docs и папки пока не поддерживаются')
    if type(meta.size) is not int or not 0<meta.size<=file_limit(meta.name):
        raise DriveImportError('Оригинал превышает лимит '+str(file_limit(meta.name)//1024//1024)+' МБ')
    if not isinstance(meta.md5_checksum,str) or not re.fullmatch('[0-9a-fA-F]{32}',meta.md5_checksum):
        raise DriveImportError('Контрольная сумма оригинала Drive недоступна; используйте ручную загрузку')
    return (meta.file_id,meta.name,meta.mime_type,meta.size,meta.md5_checksum.lower(),meta.modified_time)


def import_original(store, session_id, client, source, *, expected_sha256=None):
    snap=store.snapshot(session_id)
    ident=drive_file_id(source)
    if expected_sha256 in (None,''):expected_sha256=None
    elif not isinstance(expected_sha256,str) or not re.fullmatch('[0-9a-fA-F]{64}',expected_sha256):
        raise ValueError('Ожидаемый SHA256 должен содержать 64 шестнадцатеричных символа')
    else:expected_sha256=expected_sha256.lower()
    if client is None:raise DriveImportError('Google Drive не настроен на локальном сервере; доступ не проверен',503)
    if len(snap['files'])>=200:raise DriveImportError('Лимит диалога: 200 файлов; создайте другой диалог')
    try:
        before=validate_metadata(client.metadata(ident),ident)
        with tempfile.TemporaryDirectory(prefix='drive-import-',dir=store.root) as folder:
            target=Path(folder)/'original'
            downloaded=client.download(ident,str(target),max_bytes=file_limit(before[1]))
            during=validate_metadata(downloaded.metadata,ident)
            after=validate_metadata(client.metadata(ident),ident)
            if before!=during or before!=after:raise DriveImportError('Файл Drive изменился во время загрузки; повторите импорт')
            if target.stat().st_size!=before[3]:raise DriveImportError('Размер скачанного оригинала не совпадает')
            data=target.read_bytes()
            sha=hashlib.sha256(data).hexdigest()
            if (sha!=downloaded.source_sha256 or downloaded.bytes_written!=len(data)
                    or hashlib.md5(data,usedforsecurity=False).hexdigest()!=before[4]):
                raise DriveImportError('Контрольная сумма скачанного оригинала не совпадает')
            if expected_sha256 is not None and sha!=expected_sha256:
                raise DriveImportError('SHA256 не совпадает с ожидаемым оригиналом')
            provenance=dict(provider='GOOGLE_DRIVE',drive_file_id=ident,name=before[1],mime_type=before[2],
                            md5_checksum=before[4],modified_time=before[5],source_sha256=sha,
                            expected_sha256=expected_sha256,imported_at=time.time(),
                            scope='SOURCE_IDENTITY_ONLY',acceptance_granted=False)
        # Cleanup must succeed before registering the permanent original. A
        # cleanup failure must not report an error after a successful commit.
        return preserve_file(store,session_id,before[1],data,source_metadata=provenance)
    except DriveImportError:raise
    except Exception:
        raise DriveImportError('Не удалось импортировать Drive: проверьте OAuth, доступ к файлу и соединение. Оригинал не добавлен.',502) from None
