"""Exercise publication failures using synthetic markers in temporary repos."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    'publication_scan', Path(__file__).parents[1] / 'scripts/publication_scan.py')
SCAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAN)


class PublicationScanTests(unittest.TestCase):
    def test_private_values_and_binary_fail(self):
        samples = [('/' + 'Users/' + 'private/file').encode(),
                   ('person' + '@outside' + '.invalid').encode(),
                   ('123-' + '1234567-' + '1234567').encode(),
                   ('ghp_' + 'A' * 30).encode(), bytes([255])]
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertTrue(SCAN.inspect('synthetic', sample))
        self.assertFalse(SCAN.inspect('synthetic', b'allowed@example.invalid'))

    def test_dotenv_filename_fails_even_without_recognizable_secret(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.env').write_text('MODE=synthetic')
            with patch.object(SCAN, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    SCAN.main()

    def test_runtime_network_import_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'ops_lab').mkdir()
            (root / 'ops_lab' / 'unsafe.py').write_text('import socket\n')
            with patch.object(SCAN, 'ROOT', root), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    SCAN.main()

    def test_working_symlink_and_attachment_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'payload.pdf').write_text('synthetic')
            (root / 'shortcut').symlink_to(root / 'payload.pdf')
            output = io.StringIO()
            with patch.object(SCAN, 'ROOT', root), contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    SCAN.main()
            self.assertIn('payload.pdf: disallowed artifact', output.getvalue())
            self.assertIn('shortcut: symlink', output.getvalue())

    def test_staged_secret_fails_after_worktree_is_sanitized(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(['git', '-C', folder, 'init', '-b', 'main'], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            target = root / 'staged.txt'
            target.write_text('ghp_' + 'A' * 30)
            subprocess.run(['git', '-C', folder, 'add', 'staged.txt'], check=True)
            target.write_text('synthetic-safe')
            output = io.StringIO()
            with patch.object(SCAN, 'ROOT', root), contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    SCAN.main()
            self.assertIn('index:staged.txt: credential', output.getvalue())

    def test_deleted_historical_secret_still_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                subprocess.run(['git', '-C', folder, *args], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            git('init', '-b', 'main')
            git('config', 'user.name', 'Synthetic')
            git('config', 'user.email', 'author@example.invalid')
            target = root / 'removed.txt'
            target.write_text('ghp_' + 'A' * 30)
            git('add', 'removed.txt')
            git('commit', '-m', 'synthetic first')
            git('rm', 'removed.txt')
            git('commit', '-m', 'synthetic delete')
            output = io.StringIO()
            with patch.object(SCAN, 'ROOT', root), contextlib.redirect_stdout(output):
                with self.assertRaises(SystemExit):
                    SCAN.main()
            self.assertIn('history:removed.txt: credential', output.getvalue())


if __name__ == '__main__':
    unittest.main()
