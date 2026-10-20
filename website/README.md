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

Run `python3 -B website/build.py` from the source folder after editing content or translations. This regenerates `index.html` (ET), `ru/index.html` (RU), the runtime message bundle and eleven legacy redirects. Add the Estonian translation when changing Russian source copy: the build fails on untranslated content. Runtime UI strings use `t(...)` with entries in the runtime catalog. Service, timing and contact-method values remain the existing Russian backend enums while displayed labels are translated. Cookie dismissal is shared across both routes. Older prototype HTML/CSS files are preserved and are not linked from the active website.

## Current contact flow

Local preview runs `python3 website/server.py` at localhost:8765. The same-origin `/api/enquiry` receives multipart forms and sends through TLS-authenticated SMTP. FormSubmit has been removed. Each fresh checkout needs its own local SMTP configuration: run `python3 website/configure-mail.py` to enter a sending account and app password. Google requires 2-Step Verification for app passwords. Credentials are stored in `website/.mail-config.json` with mode 0600 and must not be committed; the server refuses all website source/config paths.

The form stays on the page and displays SMTP acceptance or an actual error. Success is not claimed when credentials are missing. Failed submissions retain user values. The customer chooses phone/email, and only the selected field is sent. Five files, 10 MB total, are validated both client-side and server-side. Requests use a short-lived HMAC token, same-origin checks, a honeypot, a three-per-10-minute IP limit, bounded concurrent sends and TLS. These deter basic abuse but are not a CAPTCHA guarantee. Local IP limits must be replaced with a deployment-specific trusted proxy policy before hosting. The stdlib HTTP server is a local preview server, not a production deployment.

No enquiries, attachments or credentials are logged, and uploaded files are held in memory only. SMTP delivery for a new checkout remains unverified until local credentials are configured and a test reaches the inbox.

## Content

Service area: Tallinn, Estonia. Do not invent reviews, completed projects, prices, qualifications or guarantees. Existing photos illustrate services; they are not a portfolio. Estonian and Russian versions are available. Real project content is still pending.

## Validation

Both language routes and shared assets return HTTP 200. JavaScript and Python syntax checks passed. DOM integration checks load the served pages and verify language links, exact scroll-position and selected-service preservation, visible/accessibility translations, gallery/menu behavior, translated form success and error messages, attachment controls, unchanged backend enum values and shared cookie dismissal. Test submissions are intercepted in memory; no enquiry emails are sent.

Detail photo strips use a transform-animated inner track so touch does not take control of the horizontal scroll offset. Keep vertical touch panning and pinch zoom enabled, preserve photo taps, and disable native image dragging and long-press callouts in animated mode. Validate touch-and-hold behavior on an actual phone: DOM simulations cannot verify native browser gesture handling.

Responsive styles cover narrow phones, tablets, and desktop navigation. Automated visual rendering remains unverified: Chromium was prevented from launching by the local sandbox's macOS Mach-port restriction.

## Single-page refactor

Header and footer navigation use native fragment links. Service rows link to detailed sections; enquiry buttons select a service and scroll to Contacts. The header stays visible, with scroll offsets and active-section indication. Privacy content expands in place. Old routes redirect to the matching anchor and preserve the service query parameter.

Validated unique IDs, one H1, every fragment destination, removal of separate-page links, mobile menu closing, enquiry selection, privacy expansion, FAQ filtering, clipboard and live HTTP responses. Browser visual testing remains subject to the sandbox limitation above.

## Responsive design preference

Apply layout adjustments to both desktop and mobile by default. Keep the service photo/text split consistent across breakpoints unless explicitly requested otherwise. Current split: 48/52 of available column space.
