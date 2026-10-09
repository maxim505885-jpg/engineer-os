"""Bounded native EMR_EXTTEXTOUTW records; no GDI rendering or table inference."""
import math
import struct

MAX_RECORDS=100000
MAX_TEXT_RECORDS=10000
MAX_TEXT_CODE_UNITS=250000
MAX_REFERENCE_JSON_BYTES=16*1024*1024


class EMFError(ValueError):pass


class EMFLimitError(EMFError):pass


def read(data):
    if len(data)<88:raise EMFError('Truncated EMF header')
    kind,size=struct.unpack_from('<II',data)
    signature,version,total,count=struct.unpack_from('<4I',data,40)
    if kind!=1 or size<88 or size%4 or size>len(data) or signature!=0x464d4520 or version!=0x10000 or total!=len(data):
        raise EMFError('Invalid EMF header')
    if count>MAX_RECORDS:raise EMFLimitError('EMF record limit')
    result=dict(status='PARSED_SOURCE_RECORDS',scope='NATIVE_EMF_TEXT_RECORDS_NOT_RENDERED',
                content_verified=False,layout_verified=False,text_records=[],bitmap_records=[],
                limitations=['EMF_GRAPHICS_NOT_RENDERED','EMF_TEXT_PLACEMENT_UNVERIFIED','EMF_FONT_MAPPING_UNVERIFIED'])
    offset=0;ordinal=0;code_units=0;ended=False
    def limitation(value):
        if value not in result['limitations']:result['limitations'].append(value)
    while offset<len(data):
        if len(data)-offset<8:raise EMFError('Truncated EMF record')
        kind,size=struct.unpack_from('<II',data,offset);ordinal+=1
        if ordinal>MAX_RECORDS:raise EMFLimitError('EMF record limit')
        if size<8 or size%4 or size>len(data)-offset or (ordinal>1 and kind==1):raise EMFError('Invalid EMF record framing')
        if kind==14:
            if size<20 or offset+size!=len(data):raise EMFError('Invalid EMF EOF')
            ended=True
        elif kind==84:
            if size<76:raise EMFError('Truncated EMF text record')
            mode,xscale,yscale=struct.unpack_from('<Iff',data,offset+24)
            if not math.isfinite(xscale) or not math.isfinite(yscale):raise EMFError('Invalid EMF text scale')
            x,y,n,string,options=struct.unpack_from('<2i3I',data,offset+36)
            code_units+=n
            if code_units>MAX_TEXT_CODE_UNITS or len(result['text_records'])>=MAX_TEXT_RECORDS:
                raise EMFLimitError('EMF text limit')
            # This reader supports the fixed EMR_EXTTEXTOUTW rectangle layout.
            if options & 0x100:raise EMFError('ETO_NO_RECT layout unsupported')
            if n and (string<76 or string%2 or string+2*n>size):raise EMFError('Invalid EMF string span')
            dx=struct.unpack_from('<I',data,offset+72)[0]
            spacing_size=n*(8 if options & 0x2000 else 4)
            if dx and (dx<76 or dx%4 or dx+spacing_size>size or (n and dx<string+2*n and string<dx+spacing_size)):
                raise EMFError('Invalid EMF spacing span')
            raw=data[offset+string:offset+string+2*n] if n else b''
            item=dict(record=ordinal,record_offset=offset,record_bytes=size,string_offset=offset+string if n else None,
                      code_units=n,options=options,graphics_mode=mode,reference_logical_units=[x,y],
                      scale=[xscale,yscale],spacing_offset=offset+dx if dx else None,text=None)
            if options & 16:
                item['glyph_indices']=list(struct.unpack('<'+'H'*n,raw));limitation('GLYPH_INDICES_NOT_DECODED')
            else:
                try:item['text']=raw.decode('utf-16le',errors='strict')
                except UnicodeError as exc:raise EMFError('Invalid EMF Unicode text') from exc
            result['text_records'].append(item)
        elif kind in {76,81}:
            from . import emf_bitmap
            bitmap=emf_bitmap.record(data,offset,size,kind,ordinal)
            if bitmap is not None:
                if len(result['bitmap_records'])>=emf_bitmap.MAX_BITMAP_RECORDS:raise EMFLimitError('EMF bitmap record limit')
                bitmap['bitmap']=len(result['bitmap_records'])+1
                result['bitmap_records'].append(bitmap);limitation('EMF_BITMAP_PAYLOADS_UNTRANSFORMED')
                if bitmap['status']=='UNAVAILABLE':limitation('EMF_BITMAP_PAYLOAD_UNAVAILABLE')
        elif kind in {77,78,79,80,114,116}:limitation('OTHER_BITMAP_RECORDS_NOT_DECODED')
        elif kind in {83,96,97,108}:limitation('OTHER_TEXT_RECORDS_NOT_DECODED')
        elif kind==70:limitation('COMMENT_CONTENT_NOT_READ')
        offset+=size
    if not ended or ordinal!=count:raise EMFError('EMF record count or EOF mismatch')
    result['record_count']=ordinal
    return result
