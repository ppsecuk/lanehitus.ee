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

The contact form uses the local SMTP endpoint. Configure mail with `python3 website/configure-mail.py`; its settings are kept in the ignored `website/.mail-config.json`. Credentials are never included in this repository. The preview server binds to loopback and is not a production server.

Run the preview-server URL boundary checks with `python3 -B -m unittest discover -s tests -v`. Tests use synthetic temporary files and do not read mail settings or send messages.

See [website/README.md](website/README.md) for implementation and validation details.
