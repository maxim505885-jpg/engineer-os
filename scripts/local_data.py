"""Stop the application before backup; restore into a new data directory."""
import argparse
from pathlib import Path
import sys
import sqlite3
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engineering.local_app.backup import create_backup,restore_backup,verify_backup


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    backup=sub.add_parser('backup');backup.add_argument('--data-dir',type=Path,required=True);backup.add_argument('--out',type=Path,required=True)
    verify=sub.add_parser('verify');verify.add_argument('archive',type=Path)
    restore=sub.add_parser('restore');restore.add_argument('archive',type=Path);restore.add_argument('--data-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.action=='backup':result=create_backup(args.data_dir,args.out)
        elif args.action=='verify':result=verify_backup(args.archive)
        else:result=restore_backup(args.archive,args.data_dir)
        print(result);return 0
    except (ValueError,RuntimeError,OSError,sqlite3.Error) as exc:
        print('Data operation failed:',str(exc),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
