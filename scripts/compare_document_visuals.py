"""Source-bound diff-pdf receipts. Pixel equality never grants acceptance."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

MAX_BYTES = 256 * 1024 * 1024


def read_regular(path, *, pdf=False):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked inputs or output directories are unsupported')
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError('Missing, empty or oversized input')
    with path.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES or (pdf and not data.startswith(b'%PDF-')):
        raise ValueError('Invalid input format or extent')
    return path, data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def new_directory(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise ValueError('Linked output directories are unsupported')
    if path.exists():
        raise ValueError('A new output directory is required')
    path.mkdir(mode=0o700, parents=True)
    return path


def compare_files(source, reference, output, *, executable, timeout=180):
    if type(timeout) is not int or not 1 <= timeout <= 1200:
        raise ValueError('Timeout must be 1..1200 seconds')
    source, source_data = read_regular(source, pdf=True)
    reference, reference_data = read_regular(reference, pdf=True)
    executable, engine_data = read_regular(executable)
    output = new_directory(output)
    # The external renderer sees private snapshots, never the original paths.
    left, right = output/'source-snapshot.pdf', output/'reference-snapshot.pdf'
    left.write_bytes(source_data)
    right.write_bytes(reference_data)
    diff = output/'differences.pdf'
    result = dict(schema='ENGINEER_OS_VISUAL_COMPARISON_V1', status='BLOCK',
        comparison_status='NOT_COMPLETED', source_sha256=sha(source_data),
        reference_sha256=sha(reference_data), engine_sha256=sha(engine_data),
        adapter_sha256=sha(Path(__file__).read_bytes()), engine='diff-pdf',
        scope='PIXEL_COMPARISON_ONLY', reference_authority_verified=False,
        document_completeness='NOT_QUALIFIED', engineering_verified=False,
        acceptance_granted=False, execution_isolation_verified=False,
        timeout_seconds=timeout, reasons=[], diff_sha256=None, exit_code=None)
    try:
        with (output/'engine.log').open('xb') as log:
            run = subprocess.run([str(executable), '--output-diff='+str(diff), str(left), str(right)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                cwd=output, timeout=timeout, check=False,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        result['exit_code'] = run.returncode
        if run.returncode in (0, 1):
            result.update(comparison_status='PASS' if run.returncode == 0 else 'DIFFERENCES_FOUND',
                status='READY_FOR_INDEPENDENT_REVIEW' if run.returncode == 0 else 'REVIEW_REQUIRED')
            if diff.exists():
                result['diff_sha256'] = sha(read_regular(diff, pdf=True)[1])
            elif run.returncode == 1:
                result.update(status='BLOCK', comparison_status='NOT_COMPLETED')
                result['reasons'].append('DIFF_ARTIFACT_MISSING')
        else:
            result['reasons'].append('ENGINE_FAILED')
    except subprocess.TimeoutExpired:
        result['reasons'].append('ENGINE_TIMEOUT')
    except (OSError, ValueError):
        result.update(status='BLOCK', comparison_status='NOT_COMPLETED')
        result['reasons'].append('ENGINE_OR_ARTIFACT_INVALID')
    for path, expected in ((source, source_data), (reference, reference_data),
                           (left, source_data), (right, reference_data), (executable, engine_data)):
        try:
            unchanged = sha(read_regular(path)[1]) == sha(expected)
        except (OSError, ValueError):
            unchanged = False
        if not unchanged:
            result.update(status='BLOCK', comparison_status='INVALIDATED')
            if 'INPUT_CHANGED' not in result['reasons']:
                result['reasons'].append('INPUT_CHANGED')
    manifest = output/'manifest.json'
    with manifest.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    if json.loads(manifest.read_text(encoding='utf-8')) != result:
        raise ValueError('Receipt readback failed')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--reference', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--executable', default=os.environ.get('ENGINEER_OS_DIFF_PDF'))
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if not args.executable:
        parser.error('--executable or ENGINEER_OS_DIFF_PDF is required')
    try:
        result = compare_files(args.source, args.reference, args.output, executable=args.executable, timeout=args.timeout)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error)+'\n')
    print(json.dumps(result, ensure_ascii=False))
    return 2 if result['status'] == 'BLOCK' else (1 if result['comparison_status'] == 'DIFFERENCES_FOUND' else 0)


if __name__ == '__main__':
    raise SystemExit(main())
