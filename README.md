# LAN Ehitus

Website for LAN OÜ, with Estonian at `/` and Russian at `/ru/`.

## Local preview

Run from the repository root with Python 3:

```sh
python3 -B website/build.py
python3 -B website/server.py
```

Open http://localhost:8765/. On macOS, `Start LAN.command` also starts the preview.

## Editing

The shared layout and Russian content live in `website/build.py`; Estonian translations are in `website/locales/et.json`. Edit `website.css` and `website.js` for styles and behavior. Rebuild after content changes. Generated pages, photos, fonts, and earlier design explorations are included.

The contact form uses same-origin SMTP endpoints. The Python preview implements them locally; OVH uses the PHP handler under `api/`, with mandatory server-verified Cloudflare Turnstile bot protection. Configure mail and the real Turnstile widget keys with `python3 website/configure-mail.py`; its settings are kept in the ignored `website/.mail-config.json`. On OVH, place that configuration outside the public site folder, following [the deployment guide](website/DEPLOY-OVH.md). Uploading the static pages alone does not install the mail backend. The loopback Python preview does not enforce Turnstile and is not a production server.

Run the preview-server URL boundary checks with `python3 -B -m unittest discover -s tests -v`. Tests use synthetic temporary files and do not read mail settings or send messages.

Run contact browser tests with `node --test tests/test_contact_client.mjs`. The opt-in PHP/Apache integration suite uses an isolated local Docker container and simulated TLS SMTP, with synthetic credentials and messages: `LAN_PHP_TESTS=1 python3 -B -m unittest discover -s tests -p test_contact_php.py -v`. It requires the pinned image documented in that test; it never contacts the live site or a real mailbox.

See [website/README.md](website/README.md) for implementation and validation details.
