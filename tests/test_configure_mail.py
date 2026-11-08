"""Check private Gmail setup using temporary paths and synthetic secrets only."""
import contextlib
import getpass
import importlib.util
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import warnings


SOURCE = Path(__file__).resolve().parents[1] / 'website' / 'configure-mail.py'
spec = importlib.util.spec_from_file_location('lan_mail_setup', SOURCE)
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class ConfigureMailTests(unittest.TestCase):
    def test_default_account_routes_mail_and_keeps_secrets_private(self):
        password = 'abcd efgh ijkl mnop'
        secret = 'synthetic-private-turnstile-key'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.mail-config.json'
            output = io.StringIO()
            with patch('builtins.input', side_effect=['', 'synthetic-public-site-key']), \
                    patch.object(setup.getpass, 'getpass', side_effect=[password, secret]), \
                    contextlib.redirect_stdout(output):
                setup.configure(path)
            config = json.loads(path.read_text())
            self.assertEqual(config['user'], 'lebjodkin.toll68@gmail.com')
            self.assertEqual(config['sender'], config['user'])
            self.assertEqual(config['recipient'], config['user'])
            self.assertEqual((config['host'], config['port']), ('smtp.gmail.com', 465))
            self.assertEqual(config['password'], password.replace(' ', ''))
            self.assertEqual(config['turnstile_secret_key'], secret)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            for value in (password, config['password'], secret):
                self.assertNotIn(value, output.getvalue())

    def test_invalid_credentials_or_test_keys_preserve_existing_file(self):
        for password, site_key, secret in (
                ('short', 'synthetic-public-site-key', 'synthetic-private-key'),
                ('abcdefghijklmnop', '1x00000000000000000000AA', 'synthetic-private-key'),
                ('abcdefghijklmnop', 'synthetic-public-site-key', '')):
            with self.subTest(password_length=len(password), site_key=site_key), \
                    tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / '.mail-config.json'
                path.write_text('synthetic prior configuration')
                with patch('builtins.input', side_effect=['', site_key]), \
                        patch.object(setup.getpass, 'getpass', side_effect=[password, secret]), \
                        self.assertRaises(SystemExit):
                    setup.configure(path)
                self.assertEqual(path.read_text(), 'synthetic prior configuration')

    def test_malformed_sender_is_rejected_before_reading_password(self):
        with patch('builtins.input', return_value='sender @gmail.com'), \
                patch.object(setup.getpass, 'getpass') as hidden, \
                self.assertRaises(SystemExit):
            setup.configure(Path('/unused-test-path'))
        hidden.assert_not_called()

    def test_echoed_password_fallback_is_refused_before_prompting(self):
        def no_terminal(_prompt):
            warnings.warn('Can not control echo on the terminal.', getpass.GetPassWarning)
            self.fail('The echoed password prompt must never be reached')

        with patch.object(setup.getpass, 'getpass', side_effect=no_terminal), \
                self.assertRaisesRegex(SystemExit, 'local terminal'):
            setup.hidden_input('Synthetic password: ')
