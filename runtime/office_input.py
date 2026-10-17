"""Bounded raw input disk, no filesystem or host-directory sharing.

Caller owns the source/staging paths. Guest validates the expected source digest
before using bytes; this format provides transport integrity, not acceptance.
"""
import hashlib
import re
import struct
from pathlib import Path

MAX_INPUT=64*1024**2
HEADER_SIZE=512
MAGIC=b'ENGINEER_OFFICE_INPUT_V1\0'

class OfficeInputError(ValueError):pass

def _identity(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):raise OfficeInputError('OFFICE_INPUT_IDENTITY')
    return bytes.fromhex(value)

def write_input_disk(source,target,expected_sha256,*,stop):
    expected=_identity(expected_sha256)
    if stop.is_set():raise OfficeInputError('OFFICE_CANCELLED')
    source=Path(source);before=source.stat();size=before.st_size
    if not 0<size<=MAX_INPUT:raise OfficeInputError('OFFICE_INPUT_SIZE')
    header=MAGIC+struct.pack('>Q',size)+expected
    digest=hashlib.sha256();total=0
    with source.open('rb') as src,Path(target).open('xb') as dst:
        dst.write(header+b'\0'*(HEADER_SIZE-len(header)))
        while chunk:=src.read(1024**2):
            if stop.is_set():raise OfficeInputError('OFFICE_CANCELLED')
            total+=len(chunk)
            if total>size:raise OfficeInputError('OFFICE_INPUT_CHANGED')
            digest.update(chunk);dst.write(chunk)
        dst.write(b'\0'*((-size)%512))
    after=source.stat()
    if total!=size or digest.digest()!=expected or (before.st_size,before.st_mtime_ns,before.st_ino)!=(after.st_size,after.st_mtime_ns,after.st_ino):
        raise OfficeInputError('OFFICE_INPUT_CHANGED')

def _exact(stream,size):
    chunks=[];remaining=size
    while remaining:
        chunk=stream.read(min(remaining,1024**2))
        if not chunk or len(chunk)>remaining:raise OfficeInputError('OFFICE_INPUT_TRUNCATED')
        chunks.append(chunk);remaining-=len(chunk)
    return b''.join(chunks)

def read_input_stream(stream,expected_sha256):
    expected=_identity(expected_sha256);header=_exact(stream,HEADER_SIZE);offset=len(MAGIC)
    if header[:offset]!=MAGIC:raise OfficeInputError('OFFICE_INPUT_HEADER')
    size=struct.unpack('>Q',header[offset:offset+8])[0]
    if not 0<size<=MAX_INPUT:raise OfficeInputError('OFFICE_INPUT_SIZE')
    if header[offset+8:offset+40]!=expected or any(header[offset+40:]):raise OfficeInputError('OFFICE_INPUT_HEADER')
    data=_exact(stream,size)
    if hashlib.sha256(data).digest()!=expected:raise OfficeInputError('OFFICE_INPUT_CHANGED')
    if any(_exact(stream,(-size)%512)) or stream.read(1):raise OfficeInputError('OFFICE_INPUT_PADDING')
    return data
