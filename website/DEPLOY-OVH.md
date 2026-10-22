# Deploy the OVH contact form

This deployment adds PHP 8.3+ handlers for `/api/token` and `/api/enquiry`, internally routed to `api/index.php` by the root `.htaccess`. The Python server remains a local preview only. OVH supports [PHP](https://docs.ovhcloud.com/en/guides/web-cloud/web-hosting/configure-your-web-hosting) and [.htaccess URL rewriting](https://docs.ovhcloud.com/en/guides/web-cloud/web-hosting/htaccess-url-rewriting-using-mod-rewrite) on shared hosting.

This is a **human-run production deployment**. The workspace instructions supplied for this session state: “Codex must not execute commands that read, create, modify, deploy, roll back, or delete in any Production or PCI-Production system.” Local preparation does not establish that the live deployment works.

## Check the hosting layout

The expected FTP layout is:

```text
/
├── lanehitus/                 # Public root folder configured in OVH
│   ├── .htaccess
│   ├── .user.ini
│   ├── index.html
│   ├── website.js
│   ├── website.i18n.js
│   ├── website.css
│   ├── ru/index.html
│   ├── api/index.php
│   └── api/vendor/phpmailer/  # PHPMailer 7.1.1 and its license
└── lanehitus-private/         # Outside every website's public root
    ├── .mail-config.json
    └── .contact-state/        # Created by the PHP handler
```

FTP `/lanehitus` is relative to the hosting account's FTP view, not the server filesystem root. The account's absolute path, PHP identity, active PHP version, extensions and permissions have not been inspected. Confirm the private sibling directory is outside **all** configured website roots and is accessible to the PHP account.

Check PHP 8.3 or newer, the `openssl`, `fileinfo` and `json` extensions, `allow_url_fopen` enabled, and writable PHP upload temporary storage. PHP must reach Cloudflare's HTTPS verification endpoint as well as the configured SMTP server; cURL is not required by this handler. Do not change the shared root `.ovhconfig` or other account-wide settings: `pavelpsec.uk` uses the same hosting account. Resolve an incompatible runtime with the hosting administrator first.

## Configure mail privately

Place the mail configuration at FTP `/lanehitus-private/.mail-config.json`. You can reuse the ignored local `website/.mail-config.json` created by `website/configure-mail.py` after adding the required Turnstile keys below; transfer it privately without printing it, committing it or putting it under `/lanehitus`.

Run `python3 website/configure-mail.py` from the local repository and enter the sending Gmail address, App Password and Turnstile keys when prompted. The helper fixes the recipient to `lebjodkin.toll68@gmail.com`; inspect its source if a different recipient is intended, rather than adding customer-controlled routing. The helper saves configuration only and does not test or send mail. Re-running it replaces the local configuration, so have all required values available privately first.

The required JSON keys are `host`, `port`, `user`, `password`, `sender`, `recipient`, `turnstile_site_key` and `turnstile_secret_key`; `port` is a number. `user` must be the full sending mailbox address, and `sender` must match it. The backend rejects missing credentials and a mismatched sender before sending. Keep `sender` and `recipient` fixed in this private configuration. The visitor's validated email is a Reply-To address, never the sender or recipient. The phone option includes the callback number in the message.

Use mode **0700** for `lanehitus-private` and **0600** for `.mail-config.json`, with ownership allowing the PHP account to read the configuration and create its private `.contact-state` directory. Runtime state contains signing secrets and rate-limit data; keep it private and writable by that account. Do not solve ownership problems with world-writable permissions.

For Gmail, use an App Password rather than the account password: port **465** uses implicit TLS; **587** uses STARTTLS. TLS certificate verification stays enabled. SMTP connectivity and credentials must be verified from the deployed PHP handler; working credentials on a laptop do not establish hosting connectivity. [PHPMailer authentication and TLS guidance](https://github.com/PHPMailer/PHPMailer/wiki/Troubleshooting).

Authenticated OVH mailbox SMTP is another supported transport; use that mailbox's documented server and credentials if chosen. Do not silently switch to native `mail()`. [OVH sending methods and sender requirements](https://docs.ovhcloud.com/en/guides/web-cloud/web-hosting/email-sending-best-practices).

### OVH unauthenticated-email warning

The PHP handler explicitly uses authenticated SMTP and verified TLS, with no fallback to PHP `mail()`. It authenticates to the provider configured in the private file: Gmail with the Gmail setup above, or an OVH mailbox when configured for OVH SMTP. SMTP credentials and the matching fixed sender are required; the customer address is used only for Reply-To. The recipient configured by `website/configure-mail.py` is `lebjodkin.toll68@gmail.com`.

Local code does not enable authenticated sending on the live host until it is uploaded and configured. A warning shown for the shared hosting account does not identify which website or script sent the unauthenticated messages. Check the other applications through the normal human production process as necessary; changing this form alone does not prove the account warning will disappear. The current code and synthetic tests do not establish the source of that warning.

## Set up Turnstile

Turnstile has a [Free plan](https://developers.cloudflare.com/turnstile/plans/) and works independently of Cloudflare DNS or proxying. Keep DNS at Zone.ee and hosting at OVH. [Independent service](https://developers.cloudflare.com/turnstile/get-started/).

1. Sign in to the [Cloudflare Turnstile dashboard](https://dash.cloudflare.com/?to=/:account/turnstile) and select **Add widget**.
2. Name it `LAN contact`. Under hostname management, add `lanehitus.ee` and `www.lanehitus.ee`, without `https://`, paths or ports. Adding the root already authorizes its subdomains; the PHP handler separately accepts only these two hostnames. Choose **Managed**, leave pre-clearance disabled, then select **Create**. [Dashboard steps](https://developers.cloudflare.com/turnstile/get-started/widget-management/dashboard/), [hostnames](https://developers.cloudflare.com/turnstile/additional-configuration/hostname-management/).
3. Copy the widget's real **sitekey** and **secret key** into the private configuration using the helper above. The sitekey is public; the secret stays on the server. Never paste the secret into chat or page source. Managed mode may ask the visitor to tick a checkbox when needed; it is bot protection, not proof that an enquiry is from a genuine customer. No pre-clearance cookie is required for this form. [Widget behavior](https://developers.cloudflare.com/turnstile/concepts/widget/), [default token versus optional clearance cookie](https://developers.cloudflare.com/cloudflare-challenges/concepts/clearance/).

The PHP handler requires real widget keys: missing values and known Cloudflare test keys leave it unavailable. `/api/token` exposes only the public `captcha` configuration. Before SMTP, the server validates the token over verified HTTPS against `https://challenges.cloudflare.com/turnstile/v0/siteverify`, with an eight-second timeout. It requires `success: true`, hostname `lanehitus.ee` or `www.lanehitus.ee`, and action `contact`. The verification POST contains only the secret and opaque token, with no enquiry fields, attachment contents or `remoteip` parameter. Tokens expire after five minutes and can be used once. [Required server validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/).

The browser loads Cloudflare's `api.js` directly; do not self-host or cache that script. The local Python loopback preview retains its older flow without Turnstile and does not exercise the production PHP checks. Production PHP has no CAPTCHA bypass. Use synthetic provider fixtures for automated tests; never put dummy keys on the public host. [Script loading](https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/), [test keys](https://developers.cloudflare.com/turnstile/troubleshooting/testing/).

## Prepare and upload

1. Run local checks from the repository root: `python3 -B -m unittest discover -s tests -v` and `node --test tests/test_contact_client.mjs`. The PHP suite is opt-in: with local Docker and the pinned image in `tests/test_contact_php.py`, run `LAN_PHP_TESTS=1 python3 -B -m unittest discover -s tests -p test_contact_php.py -v`. Rebuild changed pages with `python3 -B website/build.py`. Backend tests use synthetic fixtures only; they must not read real mail settings or send real mail.
2. Privately back up the exact existing public files you will replace, including hidden `.htaccess` and `.user.ini`, `api/` if present, JavaScript and both language pages. Record which files are newly added. Keep backups and secrets outside public website roots.
3. Confirm the private mail configuration and directory ownership described above.
4. Upload `api/` with its vendored PHPMailer **7.1.1** files and license first. No Composer installation is needed on the host for this vendored SMTP setup. [Pinned upstream release](https://github.com/PHPMailer/PHPMailer/releases/tag/v7.1.1).
5. Upload the root `.user.ini`. It requests `post_max_size=12M`, `upload_max_filesize=10M` and `max_execution_time=60`. Keep the host's `max_file_uploads` setting above five: the application rejects more than five files and enforces **10 MB combined**, while the larger request limit allows multipart overhead. Lowering PHP's count to five can discard extra uploads before validation.
6. Merge/upload the root `.htaccess`, preserving unrelated hosting rules and the HTTPS/certificate-validation rules. Its internal `/api/token` and `/api/enquiry` routes must reach `api/index.php`.
7. Upload the matching updated `website.js`, `website.css` and `website.i18n.js`, then the regenerated `index.html` and `ru/index.html` last. Keep the generated asset query versions together; the CAPTCHA update changes these assets. Preserve older hashed image assets for cached pages.

Upload the public runtime files only. Do **not** upload `website/`, `tests/`, a deployment working directory, `.git/`, local mail settings or this guide into the document root.

PHP documents `.user.ini` support for CGI/FastCGI and a default configuration-cache interval of five minutes. Its availability and effective values on this OVH account remain unverified. The human operator must confirm the limits through restricted diagnostics or OVH support. If ignored, obtain a supported hosting adjustment before accepting large uploads; do not publish `phpinfo()` or alter shared configuration as a workaround. [PHP per-directory configuration](https://www.php.net/manual/en/configuration.file.per-user.php), [upload limits and temporary storage](https://www.php.net/manual/en/ini.core.php#ini.file-uploads).

## Verify before considering the form ready

The human operator should open `/api/token` over the site's HTTPS address and confirm JSON with `ready: true` and `captcha.provider: "turnstile"`. This checks local handler configuration; it does **not** prove valid provider credentials, Cloudflare connectivity, an SMTP connection or inbox delivery. A 404, HTML response or `ready: false` means the deployment is incomplete.

From an actual phone, send one clearly labelled test enquiry using the selected phone/email option and a small supported attachment. Confirm the success message, the intended recipient's inbox, correct callback or Reply-To information and attachment contents. Check the other contact option and both languages locally; repeat a live submission only when necessary. A success response means **the SMTP server accepted the message**, not guaranteed inbox delivery. Check spam if needed.

Verify locally that missing, expired or reused CAPTCHA tokens, wrong hostname/action and provider failure all reject the send without SMTP. On the deployed phone flow, confirm verification can complete and that blocking the provider preserves entered values and offers retry or calling the displayed phone number. Do not bypass CAPTCHA to recover from an outage.

Retain form values after a failed send. Do not enable public SMTP traces, expose configuration or tokens, or log enquiry text, contact information, attachments or credentials. Report only a sanitized error category when requesting support.

## Roll back

If validation fails, the human operator restores the exact backed-up `.htaccess`, `.user.ini`, `api/`, runtime assets and HTML from the same prior version. Remove only files recorded as newly introduced by this release, after restoring the previous pages. Preserve existing private credentials and `.contact-state`; do not delete shared files or change the other website. Verify that the prior pages and HTTPS redirects work again. A rollback to the old static deployment does not repair its missing mail backend.
