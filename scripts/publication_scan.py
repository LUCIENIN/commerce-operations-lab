"""Fail closed on public data violations in every working file and Git blob.

A focused publication gate, not a general-purpose secret detector. Manual review
and deliberate file selection are required in addition to this scan.
"""
import ast
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'private_path': r'/(?:Users|home)/[A-Za-z0-9_-]+/',
    'amazon_order_reference': r'\b\d{3}-\d{7}-\d{7}\b',
    'ipv4_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    'credential': r'(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',
    'jwt': r'\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
}
EMAIL = re.compile(r'[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
FORBIDDEN_SUFFIXES = {'.eml', '.pdf', '.docx', '.xlsx', '.pem', '.key', '.env', '.enc'}
RUNTIME_IMPORTS = {'socket', 'subprocess', 'urllib', 'http', 'smtplib', 'imaplib',
                   'requests', 'os', 'keyring', 'ctypes', 'importlib'}


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def inspect(label: str, data: bytes) -> list[str]:
    filename = Path(label.removeprefix('history:').removeprefix('index:'))
    if (filename.suffix in FORBIDDEN_SUFFIXES or filename.name == '.env'
            or filename.name.startswith('.env.')):
        return [label + ': disallowed artifact']
    try:
        content = data.decode('utf-8')
    except UnicodeDecodeError:
        return [label + ': binary file requires explicit review']
    errors = [label + ': ' + name for name, pattern in PATTERNS.items()
              if re.search(pattern, content)]
    for address in EMAIL.findall(content):
        if not address.endswith('@example.invalid'):
            errors.append(label + ': non-synthetic email')
    return errors


def main():
    errors, working_count, blob_count = [], 0, 0
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if any(part in {'.git', '__pycache__', '.venv', '.DS_Store'} for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(str(relative) + ': symlink')
            continue
        if not path.is_file():
            continue
        working_count += 1
        errors.extend(inspect(str(relative), path.read_bytes()))
    for path in (ROOT / 'ops_lab').glob('*.py'):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules = ([x.name for x in node.names] if isinstance(node, ast.Import)
                       else [node.module or ''] if isinstance(node, ast.ImportFrom) else [])
            if any(module.split('.')[0] in RUNTIME_IMPORTS for module in modules):
                errors.append(path.name + ': external-operation import in runtime')
    if (ROOT / '.git').exists():
        # Include staged blobs even when the working copy has since been sanitized.
        for entry in git('ls-files', '--stage', '-z').decode().split('\0'):
            if not entry:
                continue
            metadata, name = entry.split('\t', 1)
            mode, oid, _ = metadata.split()
            if mode != '100644' and mode != '100755':
                errors.append('index:' + name + ': unsupported file mode')
            errors.extend(inspect('index:' + name, git('cat-file', '-p', oid)))
        # --all includes objects from every local branch and tag, including deleted files.
        listing = git('rev-list', '--objects', '--all').decode().splitlines()
        for item in listing:
            oid, _, name = item.partition(' ')
            if git('cat-file', '-t', oid).strip() == b'blob':
                blob_count += 1
                errors.extend(inspect('history:' + name, git('cat-file', '-p', oid)))
        for commit in git('rev-list', '--all').decode().splitlines():
            # Scan message body; author identity is separately set to public GitHub noreply.
            errors.extend(inspect('commit-message', git('show', '-s', '--format=%B', commit)))
    if errors:
        print('\n'.join(errors))
        raise SystemExit(1)
    print(f'PASS: {working_count} working files, {blob_count} historical blobs; runtime import gate passed')


if __name__ == '__main__':
    main()
