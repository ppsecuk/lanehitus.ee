"""Run locally; password never appears in terminal output or website files."""
import getpass, json, os
from pathlib import Path
path = Path(__file__).parent / '.mail-config.json'
user = input('Sending Gmail address: ').strip()
if not user or '@' not in user or any(c.isspace() for c in user): raise SystemExit('Enter a valid sending Gmail address.')
password = getpass.getpass('Gmail app password (hidden): ').replace(' ','')
if '@' not in user or len(password)!=16: raise SystemExit('Invalid address or app password length.')
settings = {'host':'smtp.gmail.com','port':465,'user':user,'password':password,'sender':user,'recipient':'lebjodkin.toll68@gmail.com'}
fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
os.chmod(path,0o600)
with os.fdopen(fd,'w') as f: json.dump(settings,f)
print('Saved locally. Restart the LAN server if needed.')
