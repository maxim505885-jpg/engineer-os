"""Bounded identity inspection of LIR originals, never binary model decoding."""
import hashlib
import io
import re
import struct
import zipfile

_HEADER=re.compile(rb'^[<U]LIRA-SAPR (\d{4}) software ver\.([A-Za-z0-9.]{1,64})\x00')


def inspect_lir(data):
    if not isinstance(data,bytes) or not 0<len(data)<=100*1024*1024:
        raise ValueError('LIR original must contain 1–100 MiB of bytes')
    match=_HEADER.match(data[:256])
    reasons=['MODEL_DECODER_UNAVAILABLE','NATIVE_MODEL_EXPORT_REQUIRED']
    if not match:reasons.append('NATIVE_HEADER_UNRECOGNIZED')
    archive=None
    stream=io.BytesIO(data)
    try:
        if zipfile.is_zipfile(stream):
            # Bound central-directory work before ZipFile allocates member objects.
            # ZIP64/large inventories remain unknown, rather than being decoded.
            offset=data.rfind(b'PK\x05\x06',max(0,len(data)-65557))
            record=data[offset:offset+22] if offset>=0 else b''
            fields=struct.unpack('<4s4H2LH',record) if len(record)==22 else None
            bounded=bool(fields and data[max(0,offset-20):max(0,offset-16)]!=b'PK\x06\x07' and fields[1]==fields[2]==0 and fields[3]==fields[4] and fields[4]<=1000 and fields[5]<=256*1024)
            if not bounded:
                reasons.append('EMBEDDED_ARCHIVE_INVENTORY_LIMIT')
                return dict(status='BLOCK',scope='NATIVE_FILE_IDENTITY_ONLY',source_sha256=hashlib.sha256(data).hexdigest(),source_bytes=len(data),
                            declared_format='LIRA-SAPR '+match[1].decode('ascii') if match else None,declared_version=match[2].decode('ascii') if match else None,
                            header_byte_span=[0,match.end()] if match else None,embedded_archive=None,semantics_decoded=False,engineering_verified=False,acceptance_granted=False,reasons=reasons)
            with zipfile.ZipFile(stream) as z:
                members=z.infolist()
                archive=dict(member_count=len(members),listed_members=[dict(name=i.filename[:200],uncompressed_bytes=i.file_size) for i in members[:100]],
                             inventory_truncated=len(members)>100,contents_decoded=False,scope='EMBEDDED_ARCHIVE_INVENTORY_ONLY')
    except (zipfile.BadZipFile,ValueError,NotImplementedError):
        reasons.append('EMBEDDED_ARCHIVE_INVENTORY_UNAVAILABLE')
    return dict(status='BLOCK',scope='NATIVE_FILE_IDENTITY_ONLY',source_sha256=hashlib.sha256(data).hexdigest(),source_bytes=len(data),
                declared_format='LIRA-SAPR '+match[1].decode('ascii') if match else None,
                declared_version=match[2].decode('ascii') if match else None,
                header_byte_span=[0,match.end()] if match else None,embedded_archive=archive,
                semantics_decoded=False,engineering_verified=False,acceptance_granted=False,reasons=reasons)
