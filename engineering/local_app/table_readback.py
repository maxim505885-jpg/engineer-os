"""Optional offline raster table candidates, bounded in a disposable worker.

Public page numbers are 1-based; bboxes are unrotated CropBox-relative PDF points.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
MAX_PIXELS = 9_000_000
MAX_TABLES = 100
MAX_CELLS = 10_000
TIMEOUT = 90
BACKENDS = ('img2table', 'paddleocr')


def read_tables(pdf_bytes, page: int, bbox: list, backend: str):
    """Return unverified JSON candidates or a stable UNAVAILABLE/ERROR envelope."""
    if backend not in BACKENDS:
        raise ValueError('INVALID_TABLE_BACKEND')
    if not isinstance(pdf_bytes, bytes) or not 0 < len(pdf_bytes) <= MAX_SOURCE_BYTES:
        raise ValueError('SOURCE_SIZE_LIMIT')
    if type(page) is not int or page < 1:
        raise ValueError('INVALID_PAGE')
    if not isinstance(bbox, list) or len(bbox) != 4 or any(type(n) not in (int, float) or not math.isfinite(n) for n in bbox):
        raise ValueError('INVALID_REGION')
    python = os.environ.get('ENGINEER_OS_TABLE_PYTHON')
    unavailable_reason = None
    if not python or not Path(python).is_absolute() or not Path(python).is_file():
        unavailable_reason = 'TABLE_PYTHON_NOT_CONFIGURED'
        python = sys.executable
    with tempfile.TemporaryDirectory(prefix='engineer-table-') as directory:
        source = Path(directory) / 'source.pdf'
        source.write_bytes(pdf_bytes)
        request = dict(source=str(source), page=page, bbox=bbox, backend=backend,
                       source_sha256=hashlib.sha256(pdf_bytes).hexdigest(),unavailable_reason=unavailable_reason)
        root = Path(__file__).resolve().parents[2]
        env = dict(os.environ, PYTHONPATH=str(root), OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
                   MKL_NUM_THREADS='1', NUMBA_NUM_THREADS='1', PADDLE_HOME=directory,
                   XDG_CACHE_HOME=directory, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                   PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True')
        # stdout is a regular bounded file: pipe buffering cannot deadlock and a
        # hostile/noisy backend cannot allocate an unbounded parent buffer.
        with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
            try:
                process = subprocess.Popen([python, '-m', 'engineering.local_app.table_worker'],
                    cwd=root, env=env, stdin=subprocess.PIPE, stdout=output, stderr=errors,
                    start_new_session=True)
            except OSError:
                result=unavailable(backend, 'TABLE_PYTHON_UNAVAILABLE')
                result.update(source_sha256=request['source_sha256'],page_no=page,source_bbox=bbox,source_geometry_validated=False)
                return result
            try:
                process.stdin.write(json.dumps(request, allow_nan=False).encode())
                process.stdin.close()
                deadline = time.monotonic() + TIMEOUT
                while process.poll() is None:
                    if os.fstat(output.fileno()).st_size > MAX_OUTPUT_BYTES or os.fstat(errors.fileno()).st_size > MAX_OUTPUT_BYTES:
                        raise ValueError('TABLE_OUTPUT_LIMIT')
                    if time.monotonic() >= deadline:
                        raise ValueError('TABLE_TIMEOUT')
                    try:
                        process.wait(timeout=min(.1,max(.001,deadline-time.monotonic())))
                    except subprocess.TimeoutExpired:
                        pass
                if os.fstat(output.fileno()).st_size > MAX_OUTPUT_BYTES or os.fstat(errors.fileno()).st_size > MAX_OUTPUT_BYTES:
                    raise ValueError('TABLE_OUTPUT_LIMIT')
                output.seek(0)
                raw = output.read(MAX_OUTPUT_BYTES + 1)
                if len(raw) > MAX_OUTPUT_BYTES:
                    raise ValueError('TABLE_OUTPUT_LIMIT')
                try:
                    result = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    raise ValueError('TABLE_WORKER_FAILED') from None
                if not isinstance(result, dict):
                    raise ValueError('TABLE_WORKER_FAILED')
                return result
            except subprocess.TimeoutExpired:
                raise ValueError('TABLE_TIMEOUT') from None
            finally:
                # Kill all descendants even when the main worker exited normally.
                try:
                    if os.name == 'nt':
                        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, OSError, subprocess.TimeoutExpired):
                    pass
                process.wait(timeout=10)


def unavailable(backend, reason):
    return dict(status='UNAVAILABLE', backend=backend, reason=reason, tables=[],
                acceptance_granted=False, quality_verified=False)
