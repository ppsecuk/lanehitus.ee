"""Create private SMTP/Turnstile settings locally without printing secrets."""
import getpass, json, os, re, warnings
from pathlib import Path

MAILBOX = 'lebjodkin.toll68@gmail.com'


def hidden_input(prompt):
    # Refuse getpass's echoed-input fallback when no private terminal is available.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            return getpass.getpass(prompt)
        except getpass.GetPassWarning:
            raise SystemExit('Run this setup in a local terminal with hidden password input.')


def configure(path):
    user = input(f'Sending Gmail address [{MAILBOX}]: ').strip() or MAILBOX
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}", user):
        raise SystemExit('Enter a valid sending Gmail address.')
    password = hidden_input('Gmail app password (hidden; not your Google password): ').replace(' ', '')
    if len(password) != 16 or not password.isascii() or not password.isalnum():
        raise SystemExit('Enter the 16-character Gmail App Password from your Google Account.')
    site_key = input('Cloudflare Turnstile site key: ').strip()
    secret_key = hidden_input('Cloudflare Turnstile secret key (hidden): ').strip()
    for value in (site_key, secret_key):
        if not re.fullmatch(r'[A-Za-z0-9_-]{10,100}', value) or re.match(r'^[123]x0{20,}', value):
            raise SystemExit('Enter the real Turnstile widget keys; published test keys are not accepted.')
    settings = {'host': 'smtp.gmail.com', 'port': 465, 'user': user, 'password': password,
                'sender': user, 'recipient': MAILBOX,
                'turnstile_site_key': site_key, 'turnstile_secret_key': secret_key}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.chmod(path, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(settings, output)
    print('Saved privately to website/.mail-config.json. No email has been sent.')
    print('Upload this file to /lanehitus-private/.mail-config.json, outside the public /lanehitus folder.')
    print('Follow website/GMAIL-SETUP.md to finish and verify delivery.')


if __name__ == '__main__':
    configure(Path(__file__).parent / '.mail-config.json')
