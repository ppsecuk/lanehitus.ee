"""Create private SMTP/Turnstile settings locally without printing secrets."""
import getpass, json, os, re
from pathlib import Path
path = Path(__file__).parent / '.mail-config.json'
user = input('Sending Gmail address: ').strip()
if not user or '@' not in user or any(c.isspace() for c in user): raise SystemExit('Enter a valid sending Gmail address.')
password = getpass.getpass('Gmail app password (hidden): ').replace(' ','')
if '@' not in user or len(password)!=16: raise SystemExit('Invalid address or app password length.')
site_key = input('Cloudflare Turnstile site key: ').strip()
secret_key = getpass.getpass('Cloudflare Turnstile secret key (hidden): ').strip()
for value in (site_key, secret_key):
    if not re.fullmatch(r'[A-Za-z0-9_-]{10,100}', value) or re.match(r'^[123]x0{20,}', value):
        raise SystemExit('Enter the real Turnstile widget keys; published test keys are not accepted.')
settings = {'host':'smtp.gmail.com','port':465,'user':user,'password':password,'sender':user,'recipient':'lebjodkin.toll68@gmail.com',
            'turnstile_site_key':site_key,'turnstile_secret_key':secret_key}
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
os.chmod(path,0o600)
with os.fdopen(fd,'w') as f: json.dump(settings,f)
print('Saved privately to website/.mail-config.json. Upload it outside the public site folder as described in website/DEPLOY-OVH.md.')
