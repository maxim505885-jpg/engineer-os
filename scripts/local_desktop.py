"""Optional native window around the existing loopback local application.

Install requirements-desktop.txt in the project environment. This starts the same
Store, Worker and server as run_local_app.py, guarded by the same data-directory
lock. No webview API bridge or cloud model key is required.
"""
import argparse
import os
from pathlib import Path
import sqlite3
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engineering.local_app.lock import DataLock
from engineering.local_app.model import LocalModel, thinking_setting
from engineering.local_app.server import make_server
from engineering.local_app.settings import active_directory, load as load_settings
from engineering.local_app.store import Store
from engineering.local_app.worker import Worker


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--selection-file', type=Path, default=ROOT / '.engineer-os/active-data-dir.txt')
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65535:
        parser.error('Port must be 0–65535')
    if sys.version_info < (3, 12):
        parser.error('Python 3.12 or newer is required')
    try:
        import webview
    except ImportError:
        print('Desktop extra is missing. Install requirements-desktop.txt in the project Python environment.', file=sys.stderr)
        return 2
    try:
        data_dir = args.data_dir or active_directory(args.selection_file, ROOT / '.engineer-os/local-app')
        settings = load_settings(data_dir)
        model = LocalModel(settings.get('ENGINEER_OS_LOCAL_MODEL_URL', 'http://127.0.0.1:11434'),
                           settings.get('ENGINEER_OS_LOCAL_MODEL', 'qwen3:8b'),
                           os.environ.get('ENGINEER_OS_LOCAL_MODEL_KEY', ''),
                           provider=settings.get('ENGINEER_OS_LOCAL_PROVIDER', 'ollama'),
                           thinking=thinking_setting(settings.get('ENGINEER_OS_LOCAL_THINK')),
                           timeout=int(settings.get('ENGINEER_OS_LOCAL_MODEL_TIMEOUT', '180')))
        with DataLock(data_dir):
            store = Store(data_dir)
            server = make_server(store, model, port=args.port, selection_path=args.selection_file)
            store.interrupt_running()
            worker = Worker(store, model)
            worker_thread = threading.Thread(target=worker.run, name='desktop-local-worker', daemon=True)
            server_thread = threading.Thread(target=server.serve_forever, name='desktop-local-server', daemon=True)
            worker_thread.start()
            server_thread.start()
            try:
                webview.create_window('ENGINEER OS', server.origin, width=1280, height=900,
                                      min_size=(800, 600))
                # No js_api bridge: the UI uses the existing authenticated loopback routes.
                webview.start(debug=False)
            finally:
                worker.stop_event.set()
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=2)
                # Keep DataLock until in-flight work finishes, just as one backend owner.
                worker_thread.join()
        return 0
    except (RuntimeError, ValueError, OSError, sqlite3.Error) as exc:
        print('Cannot start ENGINEER OS desktop:', str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
