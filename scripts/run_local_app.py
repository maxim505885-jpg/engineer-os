"""Start the local application, durable worker and browser without cloud keys."""
import argparse
import os
from pathlib import Path
import sys
import threading
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engineering.local_app.lock import DataLock
from engineering.local_app.model import LocalModel, thinking_setting
from engineering.local_app.server import make_server
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--data-dir',type=Path,default=ROOT/'.engineer-os/local-app')
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args(argv)
    if not 0<=args.port<=65535:parser.error('Port must be 0–65535')
    if sys.version_info<(3,12):parser.error('Python 3.12 or newer is required')
    origin=os.environ.get('ENGINEER_OS_LOCAL_MODEL_URL','http://127.0.0.1:11434')
    model_name=os.environ.get('ENGINEER_OS_LOCAL_MODEL','qwen3:8b')
    key=os.environ.get('ENGINEER_OS_LOCAL_MODEL_KEY','')
    try:
        model=LocalModel(origin,model_name,key,provider=os.environ.get('ENGINEER_OS_LOCAL_PROVIDER','ollama'),
                         thinking=thinking_setting(os.environ.get('ENGINEER_OS_LOCAL_THINK')))
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
    except (RuntimeError,ValueError,OSError) as exc:
        print('Cannot start ENGINEER OS:',str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
