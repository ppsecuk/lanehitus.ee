"""Local website and SMTP enquiry endpoint. Bind to loopback only."""
import base64, hashlib, hmac, json, mimetypes, secrets, smtplib, ssl, threading, time
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'website' / '.mail-config.json'
SECRET = secrets.token_bytes(32)
LOCK = threading.Lock()
ATTEMPTS = {}
SEND_SLOTS = threading.BoundedSemaphore(2)
MAX_FILES = 5
MAX_BYTES = 10_000_000
SERVICES = {'Террасы', 'Гипсокартон', 'Паркет и ламинат', 'Двери', 'Сборка мебели', 'Другая задача'}
TIMINGS = {'Пока не определился', 'В ближайшее время', 'В течение 1–3 месяцев', 'Позже'}

def config():
    if not CONFIG.exists(): return None
    value = json.loads(CONFIG.read_text())
    return value if all(value.get(k) for k in ('host', 'user', 'password', 'sender', 'recipient')) else None

def token(ip):
    stamp = str(int(time.time()))
    signature = hmac.new(SECRET, (ip + ':' + stamp).encode(), hashlib.sha256).hexdigest()
    return stamp + '.' + signature

def valid_token(value, ip):
    try:
        stamp, signature = value.split('.')
        age = time.time() - int(stamp)
        expected = hmac.new(SECRET, (ip + ':' + stamp).encode(), hashlib.sha256).hexdigest()
        return 2 <= age <= 3600 and hmac.compare_digest(signature, expected)
    except (ValueError, AttributeError): return False

def limited(ip):
    now = time.monotonic()
    with LOCK:
        for key in list(ATTEMPTS):
            ATTEMPTS[key] = [t for t in ATTEMPTS[key] if now - t < 600]
            if not ATTEMPTS[key]: del ATTEMPTS[key]
        recent = ATTEMPTS.setdefault(ip, [])
        if len(recent) >= 3: return True
        recent.append(now)
        return False

def send_message(fields, files, settings):
    message = EmailMessage()
    message['From'] = settings['sender']
    message['To'] = settings['recipient']
    message['Subject'] = 'Новая заявка LAN OÜ — ' + fields['service']
    if fields['contact_method'] == 'По email': message['Reply-To'] = fields['email']
    labels = [('Услуга','service'), ('Имя','name'), ('Способ связи','contact_method'), ('Телефон','phone'), ('Email','email'), ('Местоположение','location'), ('Когда начать','timing'), ('Описание','description')]
    message.set_content('\n\n'.join(label + ': ' + fields[key] for label,key in labels if fields.get(key)))
    for name, content, mime in files:
        main, sub = mime.split('/')
        message.add_attachment(content, maintype=main, subtype=sub, filename=name)
    context = ssl.create_default_context()
    port = int(settings.get('port', 465))
    if port == 465:
        connection = smtplib.SMTP_SSL(settings['host'], port, timeout=20, context=context)
    else:
        connection = smtplib.SMTP(settings['host'], port, timeout=20)
    with connection as smtp:
        if port != 465: smtp.starttls(context=context)
        smtp.login(settings['user'], settings['password'])
        refused = smtp.send_message(message)
        if refused: raise smtplib.SMTPRecipientsRefused(refused)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *_): pass  # Do not log customer data or credentials.
    def reply(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/token':
            self.reply(200, {'token':token(self.client_address[0]), 'ready':bool(config())}); return
        if any(part in ('.', '..') for part in unquote(path).split('/')):
            self.send_error(404); return
        try:
            resolved = Path(self.translate_path(path)).resolve()
            relative = resolved.relative_to(ROOT)
        except (OSError, ValueError):
            self.send_error(404); return
        canonical = '/' + relative.as_posix() if relative.parts else '/'
        allowed = canonical in ('/', '/index.html', '/ru', '/ru/index.html', '/robots.txt', '/sitemap.xml', '/website.js', '/website.i18n.js', '/website.css', '/lan-ehitus.svg') or canonical.startswith(('/images/', '/fonts/')) or (canonical.startswith('/service-') and canonical.endswith('.jpg')) or canonical == '/preview-room.jpg'
        if not allowed or any(part.startswith('.') for part in relative.parts):
            self.send_error(404); return
        super().do_GET()
    def do_HEAD(self):
        self.send_error(405)
    def do_POST(self):
        if self.path != '/api/enquiry': self.reply(404, {'error':'Не найдено.'}); return
        origin = self.headers.get('Origin', '')
        if origin not in ('http://localhost:8765', 'http://127.0.0.1:8765'):
            self.reply(403, {'error':'Обновите страницу и повторите отправку.'}); return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= MAX_BYTES + 100_000: raise ValueError('Максимум 10 МБ вложений.')
            content_type = self.headers.get('Content-Type', '')
            if not content_type.startswith('multipart/form-data;'): raise ValueError('Некорректная форма.')
            self.connection.settimeout(30)
            body = self.rfile.read(length)
            if len(body) != length: raise ValueError('Не удалось загрузить файлы полностью.')
            message = BytesParser(policy=policy.default).parsebytes(('Content-Type: '+content_type+'\r\nMIME-Version: 1.0\r\n\r\n').encode() + body)
            fields, files = {}, []
            for part in message.iter_parts():
                key = part.get_param('name', header='content-disposition')
                data = part.get_payload(decode=True) or b''
                filename = part.get_filename()
                if filename:
                    suffix = Path(filename).suffix.lower()
                    types = {'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.heic':'image/heic','.heif':'image/heif','.pdf':'application/pdf'}
                    if suffix not in types: raise ValueError('Допустимы изображения и PDF.')
                    files.append((Path(filename.replace('\\','/')).name, data, types[suffix]))
                elif key:
                    if len(data) > 12000: raise ValueError('Слишком длинное поле.')
                    fields[key] = data.decode('utf-8')
            if fields.get('_honey') or not valid_token(fields.get('_token'), self.client_address[0]):
                self.reply(400, {'error':'Обновите страницу и попробуйте ещё раз.'}); return
            if limited(self.client_address[0]): self.reply(429, {'error':'Слишком много попыток. Попробуйте через 10 минут.'}); return
            if len(files)>MAX_FILES or sum(len(f[1]) for f in files)>MAX_BYTES: raise ValueError('Максимум 5 файлов и 10 МБ суммарно.')
            if fields.get('service') not in SERVICES or fields.get('location') not in {'Tallinn','Harjumaa','Muu'} or fields.get('timing') not in TIMINGS: raise ValueError('Выберите услугу, местоположение и сроки.')
            if not 1 <= len(fields.get('description','').strip()) <= 2500 or len(fields.get('name',''))>100: raise ValueError('Проверьте описание и имя.')
            method = fields.get('contact_method')
            if method == 'По email':
                address = fields.get('email','')
                if not (3 <= len(address)<=254 and '@' in address and not any(c.isspace() for c in address)): raise ValueError('Укажите корректный email.')
                fields.pop('phone',None)
            elif method == 'По телефону':
                phone = fields.get('phone','').strip()
                if not 5 <= len(phone)<=40 or not all(c in '+0123456789 ()-' for c in phone): raise ValueError('Укажите корректный телефон.')
                fields.pop('email',None)
            else: raise ValueError('Выберите способ связи.')
            settings = config()
            if not settings: self.reply(503, {'error':'Отправка временно недоступна. Пожалуйста, позвоните нам.'}); return
            if not SEND_SLOTS.acquire(blocking=False): self.reply(429, {'error':'Повторите отправку чуть позже.'}); return
            try: send_message(fields, files, settings)
            finally: SEND_SLOTS.release()
            self.reply(200, {'ok':True})
        except (ValueError, UnicodeError): self.reply(400, {'error':'Проверьте поля и файлы. Максимум 5 файлов, 10 МБ суммарно.'})
        except (OSError, smtplib.SMTPException): self.reply(502, {'error':'Не удалось подтвердить отправку. Пожалуйста, позвоните нам.'})

if __name__ == '__main__':
    print('LAN website: http://localhost:8765/ — SMTP '+('configured' if config() else 'not configured'), flush=True)
    ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
