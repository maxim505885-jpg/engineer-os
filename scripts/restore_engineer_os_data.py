"""Validated ENGINEER OS local-data restore."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.backup import BackupError,restore_backup

def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if not args:
        print('Usage: restore_engineer_os_data.py BACKUP.zip [TARGET_DATA_DIR]',file=sys.stderr)
        return 2
    archive=Path(args[0]).expanduser()
    target=Path(args[1]).expanduser() if len(args)>1 else ROOT/'.engineer-os'/'local-app'
    try:
        result=restore_backup(archive,target)
    except (BackupError,RuntimeError,OSError) as exc:
        print('ENGINEER OS DATA RESTORE BLOCK:',exc,file=sys.stderr)
        return 2
    print('ENGINEER OS DATA RESTORE READY')
    print(result['target'])
    return 0

if __name__=='__main__':
    raise SystemExit(main())
