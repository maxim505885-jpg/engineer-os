"""Disposable, read-only source region worker with bounded JSON output."""
import json,sys
from .region_readback import recognize,MAX_OUTPUT_BYTES

def main():
    try:
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536:raise ValueError('REGION_REQUEST_LIMIT')
        request=json.loads(raw)
        result=recognize(request['source'],request['page'],request['bbox'],request['sha256'],request['ocr'],request.get('ocr_psm',6),request.get('ocr_preprocess','none'),request.get('ocr_language','rus+eng'))
        result['limitations']=[v for v in result['limitations'] if v!='NATIVE_RENDER_CALLS_REQUIRE_PROCESS_ISOLATION_FOR_HARD_DEADLINE']
        result['process_isolated']=True
        output=json.dumps(dict(result=result),ensure_ascii=False,allow_nan=False).encode()
        if len(output)>MAX_OUTPUT_BYTES:raise ValueError('REGION_OUTPUT_LIMIT')
    except Exception as exc:
        output=json.dumps(dict(error=str(exc)[:200] if isinstance(exc,ValueError) else 'REGION_READ_FAILED')).encode()
    sys.stdout.buffer.write(output)

if __name__=='__main__':main()
