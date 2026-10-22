"""Opt-in local Apache/PHP/SMTP/Turnstile integration; no external requests.

LAN_PHP_TESTS=1 python3 -m unittest discover -s tests -p test_contact_php.py -v
Requires the pinned official PHP Docker image already pulled locally. All form
values, credentials, certificates, SMTP delivery, captcha verification, and stored
mail are synthetic. Both provider hostnames resolve to container loopback only.
"""
import base64
from email import policy
from email.parser import BytesParser
import http.client
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests' / 'fixtures'
IMAGE = 'php:8.3-apache@sha256:1b8b5b0f31cc4552fa3da2f0f02556a8207cbca6e86ec4882ff7b6a644c84a2b'
DOCKER = ['docker', '--host', 'unix:///var/run/docker.sock']
PNG = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j7L0AAAAASUVORK5CYII=')


@unittest.skipUnless(os.environ.get('LAN_PHP_TESTS') == '1',
                     'Set LAN_PHP_TESTS=1 for isolated local Docker integration')
class ContactPHPTests(unittest.TestCase):
    @classmethod
    def docker(cls, *args, check=True):
        return subprocess.run(DOCKER + list(args), check=check, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='lan-contact-php-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.private = Path(cls.temp.name)
        cls.config_path = cls.private / '.mail-config.json'
        cls.config = {
            'host': 'mail.test', 'port': 465, 'user': 'test@example.test',
            'password': 'test-only', 'sender': 'test@example.test',
            'recipient': 'owner@example.test',
            'ca_file': '/var/www/lanehitus-private/test-ca-bundle.pem',
            'turnstile_site_key': 'synthetic-turnstile-site-key',
            'turnstile_secret_key': 'synthetic-turnstile-secret',
        }
        for name, host in (('smtp', 'mail.test'), ('captcha', 'challenges.cloudflare.com')):
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-keyout', str(cls.private / f'{name}-key.pem'),
                '-out', str(cls.private / f'{name}-cert.pem'), '-days', '1',
                '-subj', '/CN=' + host, '-addext', 'subjectAltName=DNS:' + host,
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
        (cls.private / 'test-ca-bundle.pem').write_bytes(
            (cls.private / 'smtp-cert.pem').read_bytes() +
            (cls.private / 'captcha-cert.pem').read_bytes())
        cls.config_path.write_text(json.dumps(cls.config))
        cls.name = 'lan-contact-tests-' + secrets.token_hex(5)
        cls.addClassCleanup(cls.cleanup_container)
        cls.docker('run', '--detach', '--rm', '--pull=never', '--name', cls.name,
                   '--publish', '127.0.0.1::80', '--add-host', 'mail.test:127.0.0.1',
                   '--add-host', 'challenges.cloudflare.com:127.0.0.1',
                   '--mount', f'type=bind,source={ROOT},target=/var/www/html,readonly',
                   '--mount', f'type=bind,source={cls.private},target=/var/www/lanehitus-private',
                   '--mount', f'type=bind,source={FIXTURES},target=/contact-fixtures,readonly',
                   IMAGE, 'sh', '/contact-fixtures/contact-apache.sh')
        binding = cls.docker('port', cls.name, '80/tcp').stdout.strip()
        cls.port = int(binding.rsplit(':', 1)[1])
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                status, _, _ = cls.request('GET', '/api/token')
                if (status == 200 and (cls.private / 'smtp-ready').exists()
                        and (cls.private / 'captcha-ready').exists()):
                    return
            except (OSError, http.client.HTTPException):
                pass
            time.sleep(0.1)
        logs = cls.docker('logs', cls.name, check=False)
        raise RuntimeError('Local PHP fixture did not become ready: ' +
                           (logs.stdout + logs.stderr)[-3000:])

    @classmethod
    def cleanup_container(cls):
        if getattr(cls, 'name', None):
            # Restore host ownership of disposable fixtures before removing the
            # container, including on Linux hosts where bind mount UIDs are real.
            cls.docker('exec', cls.name, 'chown', '-R', f'{os.getuid()}:{os.getgid()}',
                       '/var/www/lanehitus-private', check=False)
            cls.docker('rm', '--force', cls.name, check=False)

    def setUp(self):
        # Mutate synthetic fixtures from the container side of the bind mount;
        # this avoids host/VM file propagation races on Docker Desktop.
        self.php_fixture('''
            $directory = "/var/www/lanehitus-private/";
            file_put_contents($directory . ".mail-config.json", $argv[1]);
            file_put_contents($directory . "smtp-mode", "accept");
            file_put_contents($directory . "smtp-messages.jsonl", "");
            file_put_contents($directory . "captcha-mode", "accept");
            file_put_contents($directory . "captcha-requests.jsonl", "");
            file_put_contents($directory . "captcha-consumed.json", "{}");
            foreach (glob($directory . ".contact-state/*") as $path) {
                if (basename($path) !== "secret") { unlink($path); }
            }
        ''', json.dumps(self.config))

    @classmethod
    def php_fixture(cls, source, *args):
        return cls.docker('exec', cls.name, 'php', '-r', source, *args).stdout

    def write_configuration(self, settings):
        self.php_fixture('file_put_contents("/var/www/lanehitus-private/.mail-config.json", $argv[1]);',
                         json.dumps(settings))

    @classmethod
    def request(cls, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', cls.port, timeout=20)
        request_headers = {'Host': 'lanehitus.ee'}
        request_headers.update(headers or {})
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def token(self, wait=True):
        status, headers, body = self.request('GET', '/api/token')
        self.assertEqual(status, 200)
        self.assertIn('no-store', headers.get('Cache-Control', ''))
        result = json.loads(body)
        self.assertTrue(result['ready'])
        self.assertTrue(result['token'])
        self.assertEqual(result['expiresIn'], 3600)
        self.assertEqual(result['captcha'], {'provider': 'turnstile',
                                           'siteKey': self.config['turnstile_site_key'],
                                           'action': 'contact'})
        self.assertNotIn(self.config['turnstile_secret_key'].encode(), body)
        if wait:
            time.sleep(result.get('minDelayMs', 2000) / 1000 + 0.1)
        return result['token']

    def fields(self, token):
        return {
            'service': 'Террасы', 'name': 'Synthetic test customer',
            'contact_method': 'По email', 'email': 'customer@example.test',
            'phone': '+372 555 0000', 'location': 'Tallinn',
            'timing': 'Пока не определился',
            'description': 'Synthetic integration enquiry — not a real customer.',
            '_honey': '', '_token': token,
            'cf-turnstile-response': self.captcha_token(),
        }

    @staticmethod
    def captcha_token():
        return 'fixture-valid-' + secrets.token_hex(16)

    def submit(self, fields, files=(), origin='https://lanehitus.ee'):
        boundary = '----LANFixture' + secrets.token_hex(8)
        parts = []
        for name, value in fields.items():
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; '
                          f'name="{name}"\r\n\r\n{value}\r\n').encode())
        for name, filename, content, mime in files:
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; '
                          f'name="{name}"; filename="{filename}"\r\n'
                          f'Content-Type: {mime}\r\n\r\n').encode() + content + b'\r\n')
        parts.append(f'--{boundary}--\r\n'.encode())
        headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
        if origin is not None:
            headers['Origin'] = origin
        status, response_headers, body = self.request(
            'POST', '/api/enquiry', b''.join(parts), headers)
        self.assertIn('application/json', response_headers.get('Content-Type', ''))
        self.assertIn('no-store', response_headers.get('Cache-Control', ''))
        return status, json.loads(body)

    def messages(self):
        capture = self.php_fixture('echo file_get_contents("/var/www/lanehitus-private/smtp-messages.jsonl");')
        return [json.loads(line) for line in capture.splitlines() if line]

    def captcha_requests(self):
        capture = self.php_fixture('echo file_get_contents("/var/www/lanehitus-private/captcha-requests.jsonl");')
        return [json.loads(line) for line in capture.splitlines() if line]

    def captcha_mode(self, mode):
        self.php_fixture('file_put_contents("/var/www/lanehitus-private/captcha-mode", $argv[1]);', mode)

    def test_missing_configuration_is_not_ready(self):
        self.php_fixture('unlink("/var/www/lanehitus-private/.mail-config.json");')
        status, _, body = self.request('GET', '/api/token')
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)['ready'])
        self.assertNotIn(b'test-only', body)

    def test_missing_captcha_keys_is_not_ready(self):
        for key in ('turnstile_site_key', 'turnstile_secret_key'):
            with self.subTest(key=key):
                settings = dict(self.config)
                settings.pop(key)
                self.write_configuration(settings)
                status, _, body = self.request('GET', '/api/token')
                self.assertEqual(status, 200)
                self.assertFalse(json.loads(body)['ready'])
                status, data = self.submit(self.fields('invalid'))
                self.assertEqual(status, 503)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])
        self.assertEqual(self.captcha_requests(), [])

    def test_mismatched_authenticated_sender_is_rejected_before_sending(self):
        settings = dict(self.config)
        settings['sender'] = 'different@example.test'
        self.write_configuration(settings)
        status, _, body = self.request('GET', '/api/token')
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)['ready'])
        status, data = self.submit(self.fields('invalid'))
        self.assertEqual(status, 503)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_missing_smtp_credentials_never_fall_back_to_unauthenticated_mail(self):
        for key in ('user', 'password'):
            with self.subTest(key=key):
                settings = dict(self.config)
                settings[key] = ''
                self.write_configuration(settings)
                status, _, body = self.request('GET', '/api/token')
                self.assertEqual(status, 200)
                self.assertFalse(json.loads(body)['ready'])
                status, data = self.submit(self.fields('invalid'))
                self.assertEqual(status, 503)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_rejects_wrong_or_missing_origin(self):
        for origin in ('https://attacker.example', None):
            with self.subTest(origin=origin):
                status, data = self.submit(self.fields('invalid'), origin=origin)
                self.assertEqual(status, 403)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_rejects_invalid_and_too_fresh_tokens(self):
        for token in ('invalid', '0.invalid', self.token(wait=False)):
            with self.subTest(token=token):
                status, data = self.submit(self.fields(token))
                self.assertEqual(status, 400)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_rejects_expired_token_with_valid_signature(self):
        self.token(wait=False)
        secret = self.php_fixture('echo file_get_contents("/var/www/lanehitus-private/.contact-state/secret");')
        payload = str(int(time.time()) - 3601) + '.' + secrets.token_hex(16)
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        status, data = self.submit(self.fields(payload + '.' + signature))
        self.assertEqual(status, 400)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_valid_submission_has_fixed_sender_and_recipient_and_attachment(self):
        status, data = self.submit(self.fields(self.token()),
                                  [('attachment1', 'synthetic.png', PNG, 'image/png')])
        self.assertEqual((status, data), (200, {'ok': True}))
        delivered = self.messages()
        self.assertEqual(len(delivered), 1)
        self.assertEqual(delivered[0]['from'], 'test@example.test')
        self.assertEqual(delivered[0]['to'], ['owner@example.test'])
        message = BytesParser(policy=policy.default).parsebytes(delivered[0]['message'].encode())
        self.assertEqual(message['Reply-To'], 'customer@example.test')
        self.assertEqual(message['From'].addresses[0].addr_spec, 'test@example.test')
        self.assertEqual(message['To'].addresses[0].addr_spec, 'owner@example.test')
        self.assertIn('Террасы', str(message['Subject']))
        self.assertNotIn('+372 555 0000', message.get_body(preferencelist=('plain',)).get_content())
        attachments = list(message.iter_attachments())
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].get_filename(), 'synthetic.png')
        self.assertEqual(attachments[0].get_payload(decode=True), PNG)
        verification = self.captcha_requests()
        self.assertEqual(len(verification), 1)
        self.assertEqual(verification[0]['request'], 'POST /turnstile/v0/siteverify HTTP/1.1')
        self.assertTrue(verification[0]['validSecret'])
        self.assertFalse(verification[0]['includesRemoteIP'])

    def test_phone_submission_omits_customer_email_and_reply_to(self):
        fields = self.fields(self.token())
        fields['contact_method'] = 'По телефону'
        status, data = self.submit(fields)
        self.assertEqual((status, data), (200, {'ok': True}))
        message = BytesParser(policy=policy.default).parsebytes(self.messages()[0]['message'].encode())
        self.assertIsNone(message['Reply-To'])
        body = message.get_body(preferencelist=('plain',)).get_content()
        self.assertIn('+372 555 0000', body)
        self.assertNotIn('customer@example.test', body)

    def test_rejects_invalid_fields(self):
        fields = self.fields(self.token())
        fields['email'] = 'customer@example.test\r\nBcc: attacker@example.test'
        status, data = self.submit(fields)
        self.assertEqual(status, 400)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_rejects_executable_disguised_as_image(self):
        status, data = self.submit(self.fields(self.token()),
                                  [('attachment1', 'synthetic.jpg', b'<?php echo 1;', 'image/jpeg')])
        self.assertEqual(status, 400)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_rejects_six_attachments(self):
        files = [(f'attachment{i + 1}', f'synthetic{i}.png', PNG, 'image/png') for i in range(6)]
        status, data = self.submit(self.fields(self.token()), files)
        self.assertEqual(status, 400)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_oversized_body_returns_json_error(self):
        # Exceeds PHP post_max_size as well as the application limit.
        status, data = self.submit(self.fields(self.token()),
                                  [('attachment1', 'large.pdf', b'%PDF-1.4\n' + b'x' * 12_600_000,
                                    'application/pdf')])
        self.assertIn(status, (400, 413))
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_smtp_failure_never_reports_success_or_leaks_credentials(self):
        self.php_fixture('file_put_contents("/var/www/lanehitus-private/smtp-mode", "reject");')
        status, data = self.submit(self.fields(self.token()))
        self.assertIn(status, (502, 503))
        self.assertIn('error', data)
        response = json.dumps(data)
        for private_value in ('test-only', 'Synthetic backend failure', 'mail.test', 'PHPMailer'):
            self.assertNotIn(private_value, response)
        self.assertEqual(self.messages(), [])

    def test_untrusted_smtp_certificate_is_rejected(self):
        # Trust the local captcha provider, but reject the SMTP certificate.
        settings = dict(self.config)
        settings['ca_file'] = '/var/www/lanehitus-private/captcha-cert.pem'
        self.write_configuration(settings)
        status, data = self.submit(self.fields(self.token()))
        self.assertEqual(status, 502)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_wrong_smtp_password_is_rejected_without_disclosure(self):
        settings = dict(self.config)
        settings['password'] = 'incorrect-synthetic-password'
        self.write_configuration(settings)
        status, data = self.submit(self.fields(self.token()))
        self.assertEqual(status, 502)
        self.assertIn('error', data)
        response = json.dumps(data)
        for private_value in ('incorrect-synthetic-password', 'test-only',
                              'mail.test', 'Authentication', '535'):
            self.assertNotIn(private_value, response)
        self.assertEqual(self.messages(), [])

    def test_fourth_attempt_is_rate_limited(self):
        fields = self.fields(self.token())
        for _ in range(3):
            fields['cf-turnstile-response'] = self.captcha_token()
            self.assertEqual(self.submit(fields), (200, {'ok': True}))
        fields['cf-turnstile-response'] = self.captcha_token()
        status, data = self.submit(fields)
        self.assertEqual(status, 429)
        self.assertIn('error', data)
        self.assertEqual(len(self.messages()), 3)
        self.assertEqual(len(self.captcha_requests()), 3)

    def test_missing_or_oversized_captcha_token_is_rejected_without_sending(self):
        fields = self.fields(self.token())
        for captcha in ('', 'x' * 2049):
            with self.subTest(length=len(captcha)):
                fields['cf-turnstile-response'] = captcha
                status, data = self.submit(fields)
                self.assertEqual(status, 403)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])
        self.assertEqual(self.captcha_requests(), [])

    def test_forged_or_expired_captcha_token_is_rejected(self):
        fields = self.fields(self.token())
        for prefix in ('fixture-forged-', 'fixture-expired-'):
            with self.subTest(prefix=prefix):
                fields['cf-turnstile-response'] = prefix + secrets.token_hex(16)
                status, data = self.submit(fields)
                self.assertEqual(status, 403)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_captcha_token_cannot_be_replayed(self):
        fields = self.fields(self.token())
        self.assertEqual(self.submit(fields), (200, {'ok': True}))
        status, data = self.submit(fields)
        self.assertEqual(status, 403)
        self.assertIn('error', data)
        self.assertEqual(len(self.messages()), 1)

    def test_wrong_captcha_hostname_or_action_is_rejected(self):
        fields = self.fields(self.token())
        for mode in ('wrong-hostname', 'wrong-action'):
            with self.subTest(mode=mode):
                self.captcha_mode(mode)
                fields['cf-turnstile-response'] = self.captcha_token()
                status, data = self.submit(fields)
                self.assertEqual(status, 403)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_captcha_provider_errors_fail_closed(self):
        fields = self.fields(self.token())
        for mode in ('http-failure', 'bad-json', 'invalid-success'):
            with self.subTest(mode=mode):
                self.captcha_mode(mode)
                fields['cf-turnstile-response'] = self.captcha_token()
                status, data = self.submit(fields)
                self.assertEqual(status, 503)
                self.assertIn('error', data)
        self.assertEqual(self.messages(), [])

    def test_untrusted_captcha_certificate_is_rejected_before_smtp(self):
        settings = dict(self.config)
        settings['ca_file'] = '/var/www/lanehitus-private/smtp-cert.pem'
        self.write_configuration(settings)
        status, data = self.submit(self.fields(self.token()))
        self.assertEqual(status, 503)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])
        self.assertEqual(self.captcha_requests(), [])

    def test_failed_captcha_verifications_still_consume_rate_budget(self):
        fields = self.fields(self.token())
        for _ in range(3):
            fields['cf-turnstile-response'] = 'fixture-forged-' + secrets.token_hex(16)
            self.assertEqual(self.submit(fields)[0], 403)
        fields['cf-turnstile-response'] = self.captcha_token()
        status, data = self.submit(fields)
        self.assertEqual(status, 429)
        self.assertIn('error', data)
        self.assertEqual(self.messages(), [])
        self.assertEqual(len(self.captcha_requests()), 3)

    def test_internal_files_are_not_public(self):
        for path in ('/website/server.py', '/website/configure-mail.py',
                     '/tests/fixtures/contact-smtp.php', '/api/vendor/phpmailer/src/SMTP.php',
                     '/.mail-config.json', '/api/index.php'):
            with self.subTest(path=path):
                status, _, body = self.request('GET', path)
                self.assertIn(status, (403, 404))
                self.assertNotIn(b'test-only', body)


if __name__ == '__main__':
    unittest.main()
