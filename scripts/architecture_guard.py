"""Static import boundaries; not a sandbox or dynamic-code security audit."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_ROOTS = ('engineering/normative', 'engineering/calculation')


def audit(root):
    errors = []
    paths = sorted({p for folder in (*DOMAIN_ROOTS, 'runtime')
                    for p in (root / folder).rglob('*.py')})
    for path in paths:
        relative = path.relative_to(root).as_posix()
        domain = relative.startswith(tuple(folder + '/' for folder in DOMAIN_ROOTS))
        bridge = relative == 'engineering/calculation/solver_bridge.py'
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=relative)
        except (SyntaxError, UnicodeError, OSError):
            errors.append(f'SYNTAX_OR_READ_FAILURE: {relative}')
            continue
        package = path.relative_to(root).parts[:-1]
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level > len(package):
                        errors.append(f'INVALID_RELATIVE_IMPORT: {relative}:{node.lineno}')
                        continue
                    prefix = package[:len(package) - node.level + 1]
                    name = '.'.join((*prefix, *([] if not node.module else [node.module])))
                else:
                    name = node.module or ''
                names = [name] + [name + '.' + item.name for item in node.names]
            for name in names:
                def within(prefix):
                    return name == prefix or name.startswith(prefix + '.')
                if within('engineering.local_app') or (domain and any(within(x) for x in ('engineering.model_gateway', 'runtime'))):
                    errors.append(f'DOMAIN_DEPENDENCY: {relative}:{node.lineno}: {name}')
                if domain and not bridge and within('subprocess'):
                    errors.append(f'EXECUTION_OUTSIDE_BRIDGE: {relative}:{node.lineno}')
            if bridge and isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == 'shell' and not (isinstance(keyword.value, ast.Constant) and keyword.value.value is False):
                        errors.append(f'UNSAFE_SHELL: {relative}:{node.lineno}')
    return list(dict.fromkeys(errors))


def main():
    errors = audit(ROOT)
    print('ARCHITECTURE_GUARD=' + ('BLOCK' if errors else 'PASS'))
    for error in errors:
        print(error)
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
