"""Start the local application, durable worker and browser without cloud keys."""
import argparse
import os
from pathlib import Path
import sys
import sqlite3
import threading
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.lock import DataLock
from engineering.local_app.model import LocalModel, thinking_setting
from engineering.local_app.server import make_server
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker
from engineering.local_app.settings import load as load_settings,active_directory


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--selection-file',type=Path,default=ROOT/'.engineer-os/active-data-dir.txt')
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args(argv)
    if not 0<=args.port<=65535:parser.error('Port must be 0–65535')
    if sys.version_info<(3,12):parser.error('Python 3.12 or newer is required')
    key=os.environ.get('ENGINEER_OS_LOCAL_MODEL_KEY','')
    try:
        if args.data_dir is None:args.data_dir=active_directory(args.selection_file,ROOT/'.engineer-os/local-app')
        settings=load_settings(args.data_dir)
        origin=settings.get('ENGINEER_OS_LOCAL_MODEL_URL','http://127.0.0.1:11434')
        model_name=settings.get('ENGINEER_OS_LOCAL_MODEL','qwen3:8b')
        model=LocalModel(origin,model_name,key,provider=settings.get('ENGINEER_OS_LOCAL_PROVIDER','ollama'),
                         thinking=thinking_setting(settings.get('ENGINEER_OS_LOCAL_THINK')),
                         timeout=int(settings.get('ENGINEER_OS_LOCAL_MODEL_TIMEOUT','180')))
        with DataLock(args.data_dir):
            store=Store(args.data_dir)
            server=make_server(store,model,port=args.port)
            store.interrupt_running()
            worker=Worker(store,model)
            thread=threading.Thread(target=worker.run,name='local-model-worker',daemon=True)
            thread.start()
            print('ENGINEER OS:',server.origin,flush=True)
            print('History and files:',store.root,flush=True)
            print('Model:',model.model,'at',model.origin,flush=True)
            print('Close this console or press Ctrl+C to stop; history remains.',flush=True)
            if not args.no_browser:webbrowser.open(server.origin)
            try:server.serve_forever(poll_interval=.3)
            except KeyboardInterrupt:pass
            finally:
                worker.stop_event.set();server.server_close();thread.join(timeout=1)
        return 0
    except (RuntimeError,ValueError,OSError,sqlite3.Error) as exc:
        print('Cannot start ENGINEER OS:',str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
