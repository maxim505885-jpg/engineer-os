"""Bounded passive OLE source bitmap bytes; never activate an OLE object.

Optional olefile reads compound streams. Only root CONTENTS BMP/DIB and the
MS-OLEDS OLENativeStream bitmap form are recognized. Offsets are logical stream
byte offsets, not physical compound-file sector offsets. Source bytes and PNGs
are untransformed content candidates, never verified layout or meaning.
"""
import hashlib
import io
import struct

MAX_OLE_BYTES=32*1024*1024
MAX_STREAMS=32
MAX_DIRECTORY_ENTRIES=128
MAX_STREAM_BYTES=16*1024*1024
MAX_TOTAL_STREAM_BYTES=32*1024*1024
MAX_BITMAP_BYTES=16*1024*1024
MAX_PIXELS=16000000
MAX_NATIVE_PADDING_BYTES=64
_FREE=0xffffffff
_END=0xfffffffe
_SIGNATURE=bytes.fromhex('d0cf11e0a1b11ae1')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _preflight(data):
    """Bound directory/FAT traversal before the optional parser builds a tree."""
    if len(data)<512 or len(data)%512 or data[:8]!=_SIGNATURE:
        raise ValueError('INVALID_OLE_COMPOUND')
    minor,major,byte_order,shift,mini=struct.unpack_from('<5H',data,24)
    # v3 regular-sector files cover the original PBrush cases. Extended DIFAT
    # and v4 are deliberately unavailable, not guessed or partially traversed.
    if major!=3 or byte_order!=0xfffe or shift!=9 or mini!=6:
        raise ValueError('UNSUPPORTED_OLE_HEADER')
    directory_count,fat_count,directory,transaction,cutoff,mini_first,mini_count,difat,difat_count=struct.unpack_from('<9I',data,40)
    sectors=len(data)//512-1
    if directory_count or not 1<=fat_count<=109 or cutoff!=4096 or difat_count or difat not in {_END,_FREE}:
        raise ValueError('UNSUPPORTED_OLE_HEADER')
    if mini_count>sectors or (mini_count and mini_first>=sectors) or (not mini_count and mini_first not in {_END,_FREE}):
        raise ValueError('INVALID_OLE_MINIFAT')
    fat_sectors=struct.unpack_from('<109I',data,76)[:fat_count]
    if len(set(fat_sectors))!=fat_count or any(n>=sectors for n in fat_sectors):
        raise ValueError('INVALID_OLE_FAT')
    fat=[]
    for n in fat_sectors:fat.extend(struct.unpack_from('<128I',data,(n+1)*512))
    visited=set();directory_bytes=bytearray()
    while directory!=_END:
        if directory>=sectors or directory>=len(fat) or directory in visited or directory in fat_sectors:
            raise ValueError('INVALID_OLE_DIRECTORY')
        visited.add(directory)
        if len(visited)*4>MAX_DIRECTORY_ENTRIES:
            raise ValueError('OLE_DIRECTORY_LIMIT')
        directory_bytes.extend(data[(directory+1)*512:(directory+2)*512])
        directory=fat[directory]
    entries=[]
    for offset in range(0,len(directory_bytes),128):
        raw=directory_bytes[offset:offset+128];length,kind=struct.unpack_from('<HB',raw,64)
        if not kind:entries.append(None);continue
        if kind not in {1,2,5} or length<2 or length>64 or length%2 or raw[length-2:length]!=b'\x00\x00':
            raise ValueError('INVALID_OLE_DIRECTORY')
        try:name=raw[:length-2].decode('utf-16-le')
        except UnicodeError as exc:raise ValueError('INVALID_OLE_DIRECTORY') from exc
        start,length_bytes=struct.unpack_from('<IQ',raw,116)
        if length_bytes>MAX_OLE_BYTES or length_bytes>>32 or (kind==2 and length_bytes>MAX_STREAM_BYTES):
            raise ValueError('OLE_STREAM_BYTE_LIMIT')
        left,right,child=struct.unpack_from('<3I',raw,68)
        entries.append((name,kind,left,right,child))
    if not entries or not entries[0] or entries[0][1]!=5:
        raise ValueError('INVALID_OLE_DIRECTORY')
    pending=[entries[0][4]];seen=set()
    while pending:
        sid=pending.pop()
        if sid==_FREE:continue
        if sid==0 or sid>=len(entries) or sid in seen or entries[sid] is None:
            raise ValueError('INVALID_OLE_DIRECTORY')
        seen.add(sid);name,kind,left,right,child=entries[sid]
        if kind==5 or (kind==2 and child!=_FREE):raise ValueError('INVALID_OLE_DIRECTORY')
        pending.extend((left,right,child))
    if seen!={i for i,n in enumerate(entries) if i and n is not None}:
        raise ValueError('INVALID_OLE_DIRECTORY')


def _bitmap(raw,base):
    result=dict(status='UNAVAILABLE',bitmap_offset=base,scope='OLE_BITMAP_STREAM_UNTRANSFORMED',
                content_verified=False,layout_verified=False)
    payload=memoryview(raw)[base:]
    bmp=bytes(payload[:2])==b'BM';result['format']='BMP' if bmp else 'DIB'
    header=14 if bmp else 0
    if len(payload)<header+40:
        result['reason']='TRUNCATED_BITMAP_HEADER';return result
    if bmp:
        declared,reserved1,reserved2,bits_offset=struct.unpack_from('<IHHI',payload,2)
        if reserved1 or reserved2 or declared<54 or declared>len(payload):
            result['reason']='INVALID_BMP_SPAN';return result
    else:declared=len(payload);bits_offset=40
    size,width,height,planes,depth,compression,image_bytes,xppm,yppm,colors,important=struct.unpack_from('<IiiHH6I',payload,header)
    result.update(width=width,height=abs(height),top_down=height<0,bit_depth=depth,compression=compression)
    if width<=0 or not height or width*abs(height)>MAX_PIXELS or declared>MAX_BITMAP_BYTES:
        result['reason']='BITMAP_PIXEL_OR_BYTE_LIMIT';return result
    if size!=40 or planes!=1 or depth not in {24,32} or compression or colors or important or bits_offset!=header+40:
        result['reason']='UNSUPPORTED_DIB_FORMAT';return result
    stride=((width*depth+31)//32)*4;length=stride*abs(height)
    if image_bytes not in {0,length} or bits_offset+length!=declared:
        result['reason']='BITMAP_ROW_SIZE_MISMATCH';return result
    trailing=len(payload)-declared
    if trailing>MAX_NATIVE_PADDING_BYTES or any(payload[declared:]):
        result['reason']='UNSUPPORTED_BITMAP_TRAILING_DATA';return result
    result.update(status='AVAILABLE',bitmap_bytes=declared,bitmap_sha256=_sha(payload[:declared]),
                  bits_offset=base+bits_offset,bits_bytes=length,stride=stride,trailing_bytes=trailing)
    return result


def _inspect(data):
    result=dict(status='UNAVAILABLE',scope='OLE_SOURCE_BITMAP_UNTRANSFORMED',content_verified=False,
                layout_verified=False,bitmaps=[],limitations=['OLE_NOT_ACTIVATED','SOURCE_BITMAP_LAYOUT_UNVERIFIED'])
    if not isinstance(data,(bytes,bytearray)):
        result['reason']='INVALID_OLE_INPUT';return result,{}
    if len(data)>MAX_OLE_BYTES:
        result['reason']='OLE_BYTE_LIMIT';return result,{}
    result.update(bytes=len(data),sha256=_sha(data))
    try:
        import olefile
    except ImportError:
        result['reason']='OLEFILE_UNAVAILABLE';return result,{}
    try:
        _preflight(data)
        with olefile.OleFileIO(io.BytesIO(data),raise_defects=olefile.DEFECT_INCORRECT) as container:
            paths=container.listdir(streams=True,storages=False)
            if len(paths)>MAX_STREAMS:raise ValueError('OLE_STREAM_LIMIT')
            identities=[tuple(s.casefold() for s in p) for p in paths]
            if len(identities)!=len(set(identities)):raise ValueError('INVALID_OLE_DUPLICATE_STREAM')
            total=0
            for path in paths:
                length=container.get_size(path);total+=length
                if length<0 or length>MAX_STREAM_BYTES or total>MAX_TOTAL_STREAM_BYTES:
                    raise ValueError('OLE_STREAM_BYTE_LIMIT')
            result.update(stream_count=len(paths),total_stream_bytes=total)
            payloads={}
            for path in paths:
                if len(path)!=1 or path[0].casefold() not in {'contents','\x01ole10native'}:continue
                length=container.get_size(path)
                with container.openstream(path) as stream:raw=stream.read(MAX_STREAM_BYTES+1)
                if len(raw)!=length:raise ValueError('INVALID_OLE_STREAM_SIZE')
                info=dict(stream=list(path),stream_bytes=length,stream_sha256=_sha(raw),offset_scope='LOGICAL_STREAM_BYTES')
                base=0
                if path[0].casefold()=='\x01ole10native':
                    if len(raw)<4 or struct.unpack_from('<I',raw)[0]!=len(raw)-4:
                        info.update(status='UNAVAILABLE',reason='INVALID_NATIVE_DATA_SIZE')
                        result['bitmaps'].append(info);continue
                    base=4
                info.update(_bitmap(raw,base));result['bitmaps'].append(info)
                if info['status']=='AVAILABLE':payloads[tuple(path)]=raw
            if container.parsing_issues:raise ValueError('OLE_PARSING_DEFECT')
            if payloads:result['status']='AVAILABLE'
            else:result['reason']='NO_SUPPORTED_BITMAP_STREAM' if not result['bitmaps'] else 'OLE_BITMAP_UNAVAILABLE'
            return result,payloads
    except (ValueError,OSError,EOFError,struct.error,UnicodeError,RecursionError,IndexError) as exc:
        # Parser diagnostics may contain arbitrary source strings. Return stable
        # reasons only; never copy source labels/paths into an executable context.
        reason=str(exc)
        result['reason']=reason if reason.startswith(('OLE_','INVALID_','UNSUPPORTED_')) and len(reason)<80 else 'INVALID_OLE_COMPOUND'
        result['status']='UNAVAILABLE';result['bitmaps']=[]
        return result,{}


def describe(data):
    """Return bounded source stream/payload identities without bitmap execution."""
    return _inspect(data)[0]


def _selected(data,stream):
    descriptor,payloads=_inspect(data)
    if descriptor['status']!='AVAILABLE':raise ValueError('OLE bitmap unavailable: '+descriptor.get('reason',''))
    if stream is None:
        if len(payloads)!=1:raise ValueError('Ambiguous OLE bitmap stream')
        identity=next(iter(payloads))
    elif isinstance(stream,str):identity=(stream,)
    elif isinstance(stream,(list,tuple)) and all(isinstance(s,str) for s in stream):identity=tuple(stream)
    else:raise ValueError('Invalid OLE bitmap stream selector')
    if identity not in payloads:raise ValueError('OLE bitmap stream unavailable')
    info=next(b for b in descriptor['bitmaps'] if tuple(b['stream'])==identity)
    return payloads[identity],info


def extract(data,stream=None):
    """Return exact BMP/DIB bytes at the validated logical source stream span."""
    raw,info=_selected(data,stream);offset=info['bitmap_offset']
    return raw[offset:offset+info['bitmap_bytes']]


def render(data,stream=None):
    """Decode bounded BI_RGB bytes to a derived PNG; no OLE/GDI activation."""
    from PIL import Image
    raw,info=_selected(data,stream)
    mode='BGR' if info['bit_depth']==24 else 'BGRX'
    image=Image.frombytes('RGB',(info['width'],info['height']),raw[info['bits_offset']:info['bits_offset']+info['bits_bytes']],
                          'raw',mode,info['stride'],1 if info['top_down'] else -1)
    output=io.BytesIO()
    try:image.save(output,format='PNG')
    finally:image.close()
    return output.getvalue()
