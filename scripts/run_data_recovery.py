"""Browser-only offline data maintenance; no worker or model is started."""
import argparse
from pathlib import Path
import sys
from types import SimpleNamespace
import webbrowser
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.server import make_server
from engineering.local_app.settings import active_directory


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--selection-file',type=Path,default=ROOT/'.engineer-os/active-data-dir.txt')
    parser.add_argument('--port',type=int,default=0)
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args(argv)
    if not 0<=args.port<=65535:parser.error('Port must be 0–65535')
    if sys.version_info<(3,12):parser.error('Python 3.12 or newer is required')
    try:
        # An unavailable selected disk must not prevent restoration or choosing the old root.
        try:root=args.data_dir or active_directory(args.selection_file,ROOT/'.engineer-os/local-app')
        except ValueError:root=ROOT/'.engineer-os/local-app'
        server=make_server(SimpleNamespace(root=root),None,port=args.port,drive_client=None,recovery_only=True,selection_path=args.selection_file)
        print('ENGINEER OS recovery:',server.origin,flush=True)
        if not args.no_browser:webbrowser.open(server.origin)
        try:server.serve_forever(poll_interval=.3)
        except KeyboardInterrupt:pass
        finally:server.server_close()
        return 0
    except (ValueError,RuntimeError,OSError) as exc:
        print('Cannot open recovery:',str(exc),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
