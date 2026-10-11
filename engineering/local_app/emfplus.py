"""EMF+ source inventory only: no graphics execution, rendering or content verification."""
import hashlib
import collections
import json
import math
import struct
from .emf_text import EMFError,EMFLimitError

NAMES={0x4001:'Header',0x4002:'EndOfFile',0x4003:'Comment',0x4004:'GetDC',0x4008:'Object',0x4009:'Clear',0x400a:'FillRects',0x400b:'DrawRects',0x400c:'FillPolygon',0x400d:'DrawLines',0x400e:'FillEllipse',0x400f:'DrawEllipse',0x4010:'FillPie',0x4011:'DrawPie',0x4012:'DrawArc',0x4013:'FillRegion',0x4014:'FillPath',0x4015:'DrawPath',0x4016:'FillClosedCurve',0x4017:'DrawClosedCurve',0x4018:'DrawCurve',0x4019:'DrawBeziers',0x401a:'DrawImage',0x401b:'DrawImagePoints',0x401c:'DrawString',0x4025:'Save',0x4026:'Restore',0x4027:'BeginContainer',0x4028:'BeginContainerNoParams',0x4029:'EndContainer',0x402a:'SetWorldTransform',0x402b:'ResetWorldTransform',0x402c:'MultiplyWorldTransform',0x402d:'TranslateWorldTransform',0x402e:'ScaleWorldTransform',0x402f:'RotateWorldTransform',0x4030:'SetPageTransform',0x4031:'ResetClip',0x4032:'SetClipRect',0x4033:'SetClipPath',0x4034:'SetClipRegion',0x4035:'OffsetClip',0x4036:'DrawDriverString',0x4037:'StrokeFillPath',0x4038:'SerializableObject',0x4039:'SetTSGraphics',0x403a:'SetTSClip'}
NAMES.update({0x401d:'SetRenderingOrigin',0x401e:'SetAntiAliasMode',0x401f:'SetTextRenderingHint',0x4020:'SetTextContrast',0x4021:'SetInterpolationMode',0x4022:'SetPixelOffsetMode',0x4023:'SetCompositingMode',0x4024:'SetCompositingQuality'})
OBJECT_NAMES={1:'Brush',2:'Pen',3:'Path',4:'Region',5:'Image',6:'Font',7:'StringFormat',8:'ImageAttributes',9:'CustomLineCap'}

def category(kind):
    if kind in {0x4008,0x4038}:return 'OBJECT'
    if 0x4009<=kind<=0x401c or kind in {0x4036,0x4037}:return 'DRAWING'
    if 0x401d<=kind<=0x4035 or kind in {0x4039,0x403a}:return 'STATE'
    if 0x4001<=kind<=0x4004:return 'CONTROL'
    return 'UNKNOWN'


def version(value):
    if value>>12!=0xdbc01:raise EMFError('Invalid EMF+ graphics signature')


def finite(raw):
    if len(raw)%4 or any(not math.isfinite(v[0]) for v in struct.iter_unpack('<f',raw)):
        raise EMFError('Invalid EMF+ finite coordinates')


class Inventory:
    def __init__(self,record_limit,byte_limit,json_limit=16*1024*1024):
        self.records=[];self.gaps=[];self.started=False;self.ended=False;self.pending={}
        self.record_limit=record_limit;self.byte_limit=byte_limit;self.json_limit=json_limit;self.json_bytes=0
    def gap(self,value):
        if value not in self.gaps:self.gaps.append(value)
    def read(self,data,absolute,comment_ordinal,emf_record):
        if not data:raise EMFError('Empty EMF+ comment')
        offset=0
        while offset<len(data):
            if len(data)-offset<12:raise EMFError('Truncated EMF+ record')
            kind,flags,size,n=struct.unpack_from('<HHII',data,offset)
            if size<12 or size%4 or n%4 or size!=12+n or size>len(data)-offset:raise EMFError('Invalid EMF+ record framing')
            if len(self.records)>=self.record_limit:raise EMFLimitError('EMF+ record limit')
            if self.ended:raise EMFError('EMF+ records after EOF')
            if not self.started and (kind!=0x4001 or emf_record!=2):raise EMFError('EMF+ header must follow EMF header')
            raw=data[offset+12:offset+size]
            item=dict(record=len(self.records)+1,comment_record=comment_ordinal,emf_record=emf_record,
                      record_offset=absolute+offset,record_bytes=size,data_offset=absolute+offset+12,
                      data_bytes=n,type=kind,type_hex=f'0x{kind:04X}',type_name='EmfPlus'+NAMES[kind] if kind in NAMES else 'UNKNOWN',
                      flags=flags,category=category(kind),sha256=hashlib.sha256(data[offset:offset+size]).hexdigest(),
                      content_verified=False,layout_verified=False,render_verified=False)
            if kind==0x4001:
                if self.started or n!=16:raise EMFError('Invalid EMF+ header')
                v,pflags,x,y=struct.unpack('<4I',raw);version(v);self.started=True
                item.update(graphics_version=v,emfplus_flags=pflags,logical_dpi=[x,y],dual=bool(flags&1))
            elif kind==0x4002:
                if n:raise EMFError('Invalid EMF+ EOF')
                self.ended=True
            elif kind==0x4008:self.object(raw,flags,item)
            elif item['category']=='UNKNOWN':self.gap('UNKNOWN_RECORD')
            elif item['category']=='OBJECT':self.gap('OBJECT_PAYLOAD_UNREAD')
            elif item['category']=='DRAWING':
                self.validate_drawing(kind,flags,raw)
                self.gap('DRAWING_NOT_RENDERED');item['coverage']='INVENTORIED_NOT_RENDERED'
            elif item['category']=='STATE':
                # Floating-point transform fields are inspected only for the known fixed forms.
                expected={0x402a:24,0x402c:24,0x402d:8,0x402e:8,0x402f:4,0x4030:4,0x4032:16,0x4035:8}
                if kind in expected:
                    if n!=expected[kind]:raise EMFError('Invalid EMF+ state data size')
                    finite(raw)
                elif kind in {0x402b,0x4031} and n:raise EMFError('Invalid EMF+ state data size')
                self.gap('GRAPHICS_STATE_NOT_APPLIED')
            elif kind==0x4003:self.gap('EMFPLUS_COMMENT_UNREAD')
            self.json_bytes+=len(json.dumps(item,ensure_ascii=False).encode('utf-8'))
            if self.json_bytes>self.json_limit:raise EMFLimitError('EMF+ inventory JSON limit')
            self.records.append(item);offset+=size
    def validate_drawing(self,kind,flags,raw):
        # Counted rectangles/points are validated before any allocation. Other drawing payloads stay opaque.
        if kind in {0x400a,0x400b,0x400c,0x400d,0x4019}:
            count_offset=4 if kind in {0x400a,0x400c} else 0
            if len(raw)<count_offset+4:raise EMFError('Truncated EMF+ drawing count')
            count=struct.unpack_from('<I',raw,count_offset)[0]
            if count>100000:raise EMFLimitError('EMF+ drawing element limit')
            stride=(8 if flags&0x4000 else 16) if kind in {0x400a,0x400b} else (4 if flags&0x4000 else 8)
            start=count_offset+4
            if flags&0x0800 and kind in {0x400c,0x400d,0x4019}:
                self.gap('RELATIVE_POINT_ENCODING_UNREAD');return
            if len(raw)!=start+count*stride:raise EMFError('Invalid EMF+ drawing count span')
            if not flags&0x4000:finite(raw[start:])
        else:self.gap('DRAWING_PAYLOAD_UNREAD')
    def object(self,raw,flags,item):
        identity=flags&255;kind=(flags>>8)&127;continues=bool(flags&0x8000)
        if identity>63:raise EMFError('Invalid EMF+ object identity')
        item.update(object_id=identity,object_type=kind,object_type_name=OBJECT_NAMES.get(kind,'UNKNOWN'),continues=continues)
        payload=raw;total=None
        if continues:
            if len(raw)<4:raise EMFError('Truncated EMF+ continued object')
            total=struct.unpack_from('<I',raw)[0];payload=raw[4:]
            if not total or total>self.byte_limit:raise EMFLimitError('EMF+ continued object byte limit')
        if identity in self.pending:
            pending=self.pending[identity]
            if pending['kind']!=kind or (total is not None and total!=pending['total']):raise EMFError('Ambiguous EMF+ object continuation')
            pending['bytes']+=len(payload)
            if pending['bytes']>pending['total']:raise EMFError('EMF+ continued object overflow')
            item.update(total_object_bytes=pending['total'],accumulated_object_bytes=pending['bytes'],continuation_status='CONTINUING' if continues else 'COMPLETE')
            if not continues:
                if pending['bytes']!=pending['total']:raise EMFError('Incomplete EMF+ continued object')
                del self.pending[identity]
            elif pending['bytes']>=pending['total']:raise EMFError('Invalid EMF+ continuation flag')
            self.gap('CONTINUED_OBJECT_CONTENT_UNREAD');return
        if continues:
            if len(payload)>=total:raise EMFError('Invalid EMF+ continuation size')
            self.pending[identity]={'kind':kind,'total':total,'bytes':len(payload)}
            item.update(total_object_bytes=total,accumulated_object_bytes=len(payload),continuation_status='CONTINUING')
            self.gap('CONTINUED_OBJECT_CONTENT_UNREAD');return
        item['continuation_status']='SINGLE_RECORD'
        if kind==4 and len(payload)==12:
            v,count,node=struct.unpack('<III',payload);version(v)
            if node in {0x10000002,0x10000003}:
                if count:raise EMFError('Invalid EMF+ terminal region count')
                item['object_metadata']=dict(graphics_version=v,region_node_count=count,region_kind='INFINITE' if node==0x10000003 else 'EMPTY')
                return
        self.gap('UNKNOWN_OBJECT_TYPE' if kind not in OBJECT_NAMES else 'OBJECT_PAYLOAD_UNREAD')
    def summary(self):
        if self.started and not self.ended:raise EMFError('Missing EMF+ EOF')
        if self.pending:raise EMFError('Incomplete EMF+ continued object')
        return dict(status='INVENTORIED_SOURCE_RECORDS' if self.started else 'NO_EMFPLUS_IDENTIFIED',record_count=len(self.records),
                    inventory_complete=True,category_counts=dict(collections.Counter(r['category'] for r in self.records)),
                    type_counts=dict(collections.Counter(r['type_hex'] for r in self.records)),
                    object_type_counts=dict(collections.Counter(r['object_type_name'] for r in self.records if 'object_type_name' in r)),
                    content_coverage='NOT_VERIFIED',coverage_gaps=self.gaps,
                    content_verified=False,layout_verified=False,render_verified=False)
