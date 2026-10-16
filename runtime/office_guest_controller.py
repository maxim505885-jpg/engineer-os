"""Fixed outer supervisor for the disposable offline Office guest only."""
import json
import os
from pathlib import Path
import subprocess
import sys

# Includes guest startup, input read and result emission, beyond Office's own
# 150-second conversion deadline. The host adds a separate 450-second ceiling.
CONTROL_TIMEOUT=300

def _dedicated_guest():
    return (sys.platform=='linux' and getattr(os,'geteuid',lambda:-1)()==0 and
            Path('/sys/firmware/qemu_fw_cfg/by_name/opt/eos/request/raw').is_file())

def main():
    if not _dedicated_guest():raise RuntimeError('Dedicated Office guest required')
    try:
        result=subprocess.run(['python3','/opt/engineer-office-guest.py'],check=False,timeout=CONTROL_TIMEOUT)
        return result.returncode
    except Exception as exc:
        print('ENGINEER_OFFICE_RESULT '+json.dumps(dict(code=1,error=type(exc).__name__,detail=str(exc)[:1024]),ensure_ascii=True),flush=True)
        return 1
    finally:
        try:subprocess.run(['sync'],timeout=10)
        finally:subprocess.run(['poweroff'],timeout=10)

if __name__=='__main__':raise SystemExit(main())
