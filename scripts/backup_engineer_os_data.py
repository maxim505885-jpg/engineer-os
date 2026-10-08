"""One-command ENGINEER OS local-data backup."""
from datetime import datetime
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.backup import BackupError,create_backup

def main():
    source=ROOT/'.engineer-os'/'local-app'
    destination=Path.home()/'Documents'/'ENGINEER_OS_DATA_BACKUPS'
    destination.mkdir(parents=True,exist_ok=True)
    out=destination/('engineer-os-data-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.zip')
    try:
        result=create_backup(source,out)
    except (BackupError,RuntimeError,OSError) as exc:
        print('ENGINEER OS DATA BACKUP BLOCK:',exc,file=sys.stderr)
        return 2
    print('ENGINEER OS DATA BACKUP READY')
    print(result['archive'])
    return 0

if __name__=='__main__':
    raise SystemExit(main())
