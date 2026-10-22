# LAN website

Bilingual single-page static website for LAN OÜ, Tallinn. Estonian is the default at http://localhost:8765/; Russian is at http://localhost:8765/ru/. The ET/RU links use real language routes and preserve the exact scroll coordinates, selected service, and phone/email contact mode.

## Editing

- `website/build.py`: shared layout, Russian source content and bilingual page generation.
- `website/locales/et.json`: Estonian content and runtime translations.
- `website/i18n.py`: language rendering and stable form values.
- `website.i18n.js`: generated runtime message bundle; rebuild rather than editing it directly.
- `website.css`: responsive desktop/mobile styles.
- `website.js`: mobile menu, section navigation, animated galleries, language-position restoration, service preselection, and SMTP enquiry submission.
- `lan-ehitus.svg`: existing approved-for-now logo; independent from page content.

Run `python3 -B website/build.py` from the source folder after editing content or translations. This regenerates `index.html` (ET), `ru/index.html` (RU), the runtime message bundle, crawler files and thirteen legacy redirects. Add the Estonian translation when changing Russian source copy: the build fails on untranslated content. Runtime UI strings use `t(...)` with entries in the runtime catalog. Service, timing and contact-method values remain the existing Russian backend enums while displayed labels are translated. Cookie dismissal is shared across both routes. Older prototype HTML/CSS files are preserved and are not linked from the active website.

## Image performance

Gallery previews, the logo and the portrait use responsive WebP files under `images/optimized/`. The checked-in `website/image-assets.json` maps originals to their generated sizes. Preview filenames contain a hash of the encoded bytes. Original photos stay available for the fullscreen viewer and are requested when it opens.

After adding or changing a photo, regenerate previews before building the pages:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r website/requirements-build.txt
.venv/bin/python website/optimize_images.py
python3 -B website/build.py
```

Use `.venv/bin/python website/optimize_images.py --check` to verify that previews and the manifest match their sources. Ordinary content builds use the checked-in files and do not need Pillow. Image generation preserves source files, corrects EXIF orientation and avoids upscaling. Old hashed previews are retained so cached pages continue to work.

Only the first carousel image is eager and high priority. Other active images and detail-strip thumbnails use native lazy loading. Inactive carousel images have deferred source attributes; JavaScript loads the requested slide and the next preview for a visible carousel. Navigation keeps the current image visible until its replacement is decoded. Image errors remain retryable, and fullscreen navigation uses the original photos.

## Current contact flow

Local preview runs `python3 website/server.py` at localhost:8765. The same-origin `/api/token` and `/api/enquiry` endpoints receive multipart forms and send through TLS-authenticated SMTP. On OVH Web Hosting, `api/index.php` implements those endpoints through the root `.htaccess`, using pinned PHPMailer 7.1.1. Follow [DEPLOY-OVH.md](DEPLOY-OVH.md) to install the PHP runtime files and private SMTP configuration; static HTML/JavaScript uploads alone cannot send enquiries.

Each fresh checkout needs its own private configuration: run `python3 website/configure-mail.py` to enter a sending account, app password, Turnstile site key and secret key. Credentials are stored in ignored `website/.mail-config.json` with mode 0600 and must not be committed; the preview server refuses all website source/config paths. Production PHP reads the same schema from the private sibling `lanehitus-private/.mail-config.json`, outside the document root. It stores only its signing secret, hashed-IP rate timestamps and concurrency locks in that private directory. Enquiry content and attachments are not persisted by the application.

The form stays on the page and displays SMTP acceptance or an actual error. Success is not claimed when credentials are missing. Failed submissions retain user values and attachments. Token fetches time out after ten seconds; missing/expired tokens refresh before a submission. The complete attempt has a 90-second deadline for mobile uploads, with no automatic POST retries. Only a confirmed success clears the form.

The customer chooses phone/email, and only the selected contact field is sent. Five files, 10 MB total, are validated both client-side and server-side; PHP also checks content type. PHP requests use a durable one-hour HMAC token, exact-origin checks, a honeypot, three attempts per client IP per ten minutes, two simultaneous verification/send attempts and verified TLS. Tokens do not bind to an IP, allowing a phone to switch networks. Rate limiting uses the host's REMOTE_ADDR and ignores visitor-supplied forwarding headers; the hosting administrator must verify the host supplies the client address before rollout.

Production PHP requires Cloudflare Turnstile. The private JSON must contain `turnstile_site_key` and `turnstile_secret_key`; missing keys or published dummy keys leave the API unready. Only the public site key is returned to the browser. The client explicitly renders Cloudflare's managed widget, refreshes single-use tokens after each submission, and offers a retry while retaining customer data. Russian pages use the provider's Russian UI; Estonian pages use automatic provider language selection because Turnstile does not currently list Estonian support. The surrounding form messages remain Estonian.

Before SMTP, PHP sends only the opaque CAPTCHA token and private verification secret to Cloudflare's fixed HTTPS Siteverify endpoint. It requires a successful response for `lanehitus.ee` or `www.lanehitus.ee` and action `contact`; failure, expiration, reuse, malformed replies and network/TLS problems block sending. Verification is bounded to an eight-second stream timeout and an 8 KB response. Outbound HTTPS uses PHP streams and requires `allow_url_fopen`; no cURL extension is required. The contact section discloses Cloudflare processing and links to the privacy details. CAPTCHA reduces automated abuse; it cannot prove customer intent or guarantee that no bot passes. See [Cloudflare server validation](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/).

The stdlib HTTP server remains a loopback-only preview with its original signed-token SMTP flow and no Turnstile enforcement. Browser code skips the widget only when that preview omits the CAPTCHA configuration; production PHP always requires verification regardless of browser behavior. Use the PHP integration suite for production security behavior.

No enquiries, attachments or credentials are logged by the application. PHP uses temporary upload storage, which it removes at request completion; local Python preview holds attachments in memory. SMTP delivery remains unverified until the operator configures credentials and confirms a controlled test reaches the inbox. The production runtime and delivery have not been checked by Codex.

`node --test tests/test_contact_client.mjs` exercises token expiry, slow uploads, bounded requests, localized errors and input retention with mocked transport. `LAN_PHP_TESTS=1 python3 -B -m unittest discover -s tests -p test_contact_php.py -v` runs the PHP/Apache handler against simulated TLS SMTP in a local Docker container. That opt-in suite uses only synthetic configuration and messages; see its pinned image prerequisite.

## Content

Service area: Tallinn and Harjumaa, Estonia. Do not invent reviews, completed projects, prices, qualifications or guarantees. Existing photos illustrate services; they are not a portfolio. Estonian and Russian versions are available. Real project content is still pending.

## Local search in Estonia

The two indexable content pages are Estonian `/` and Russian `/ru/`. Their titles, descriptions and H1 identify the actual construction/finishing services and Tallinn/Harjumaa coverage. `website/seo.py` adds reciprocal `et-EE`/`ru-EE` language alternatives, Estonian `x-default`, self-canonical URLs and localized social previews. The real language links remain accessible without automatic language redirects.

JSON-LD describes LAN OÜ / LAN Ehitus and the five services, using the confirmed registry code, logo and service area. It uses `Organization` and `Service`, without claiming a public street address, opening hours, reviews or a Google Business Profile. Google LocalBusiness rich-result eligibility is not established. Existing phone/email scraper deterrence is preserved; plain contact details are not added to structured data.

The build regenerates root `robots.txt` and `sitemap.xml`. The sitemap lists only the two canonical content URLs. Older bookmark redirects contain `noindex`; retired `/services/woodwork/` and `/services/renovation/` aliases lead to the current `#services` list. Apache adds `X-Robots-Tag: noindex, follow` to the earlier non-`index.html` design experiments. Keep these pages crawlable so search engines can see the indexing rule. Both crawler files are available in local preview.

Run `python3 -B -m unittest discover -s tests -v` to check metadata, locale relationships, JSON-LD, crawler files and preview access. Rebuild after changing the source copy or SEO metadata. When uploading, include the regenerated language pages, legacy redirects, `website.css`, `website.i18n.js`, `robots.txt`, `sitemap.xml` and the merged `.htaccess`, along with any pending performance assets. SEO deployment does not submit the site to search engines.

The owner confirmed that no Google Business Profile exists yet. The next external steps are to create and verify one accurate service-area profile, enter the real services and coverage, use genuine project photos, and submit the sitemap through verified Search Console access. If customers are not served at the business address, follow Google's instructions to hide that address. Record actual hours and other business details when confirmed; do not infer them from the website.

References: [Google language alternatives](https://developers.google.com/search/docs/specialty/international/localized-versions), [structured business information](https://developers.google.com/search/docs/appearance/structured-data/organization), [service-area profiles](https://support.google.com/business/answer/9157481?hl=en), and [sitemap submission](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

## OVH HTTPS redirects

The root `.htaccess` redirects HTTP and `www` requests to `https://lanehitus.ee/` with HTTP 301, preserving paths and query strings. It supports the HTTPS indicators documented for OVH Web Hosting and Cloud Web. Certificate-validation requests under `/.well-known/acme-challenge/` remain accessible without redirects.

Include this hidden file alongside `index.html` in the hosting document root. If the host already has a `.htaccess`, merge these rules before existing application rewrites rather than replacing unrelated settings. OVH must provide a valid certificate for `www.lanehitus.ee` before HTTPS requests to that hostname can reach the redirect. The Python local preview does not use `.htaccess`.

Reference: [OVH HTTPS configuration](https://docs.ovhcloud.com/en/guides/web-cloud/web-hosting/ssl-activate-https-website).

The same `.htaccess` gives static assets a 30-day browser cache, content-hashed WebP previews a one-year immutable cache, and HTML a revalidation policy. This requires Apache `mod_headers`; the rules are skipped when it is unavailable. Change the URL of any updated static asset: bump the CSS/JavaScript query version in `website/build.py`, and use a new filename or version for other assets. The image generator updates preview URLs automatically.

For deployment, upload `images/optimized/` and the matching CSS/JavaScript before the regenerated `index.html` and `ru/index.html`, then merge/upload `.htaccess`. Keep the original photos for the viewer and retain older hashed previews for cached pages. Recheck live response headers after upload because the hosting frontend can affect caching. To roll back, restore the prior HTML, CSS/JavaScript and `.htaccess`; the original photos remain available. The Python preview does not apply Apache cache rules.

## Validation

Both language routes and shared assets return HTTP 200. JavaScript and Python syntax checks passed. DOM integration checks load the served pages and verify language links, exact scroll-position and selected-service preservation, visible/accessibility translations, gallery/menu behavior, translated form success and error messages, attachment controls, unchanged backend enum values and shared cookie dismissal. Test submissions are intercepted in memory; no enquiry emails are sent.

Detail photo strips use a transform-animated inner track so touch does not take control of the horizontal scroll offset. Keep vertical touch panning and pinch zoom enabled, preserve photo taps, and disable native image dragging and long-press callouts in animated mode. Validate touch-and-hold behavior on an actual phone: DOM simulations cannot verify native browser gesture handling.

Responsive styles cover narrow phones, tablets, and desktop navigation. Automated visual rendering remains unverified: Chromium was prevented from launching by the local sandbox's macOS Mach-port restriction.

## Single-page refactor

Header and footer navigation use native fragment links. Service rows link to detailed sections; enquiry buttons select a service and scroll to Contacts. The header stays visible, with scroll offsets and active-section indication. Privacy content expands in place. Old routes redirect to the matching anchor and preserve the service query parameter.

Validated unique IDs, one H1, every fragment destination, removal of separate-page links, mobile menu closing, enquiry selection, privacy expansion, FAQ filtering, clipboard and live HTTP responses. Browser visual testing remains subject to the sandbox limitation above.

## Responsive design preference

Apply layout adjustments to both desktop and mobile by default. Keep the service photo/text split consistent across breakpoints unless explicitly requested otherwise. Current split: 48/52 of available column space.
