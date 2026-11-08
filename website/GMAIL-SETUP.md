# Send contact enquiries through Gmail

The contact form can send **from and to `lebjodkin.toll68@gmail.com`** using authenticated Gmail SMTP. For visitors who select email, their address becomes Reply-To, so replying to the enquiry reaches the visitor. For phone enquiries, the message includes the callback number.

The Estonian message “Päringu saatmine ei ole ajutiselt võimalik. Palun helistage meile.” is a generic backend-unavailable message. It can mean the API was not installed, private configuration is missing/invalid, or PHP cannot use its private state. It does not establish that Gmail rejected a message. The live hosting configuration has not been inspected.

## 1. Create the Gmail App Password

1. Sign in to Google as **`lebjodkin.toll68@gmail.com`**.
2. Enable [2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification).
3. Open [App Passwords](https://myaccount.google.com/apppasswords), create one named `LAN Ehitus website`, and save the generated 16-character password privately. Use this App Password for the form, **not your normal Google password**. Google requires 2-Step Verification for App Passwords; some security/account configurations do not offer them. [Google instructions](https://support.google.com/accounts/answer/185833?hl=en).

Do not paste the App Password into chat, HTML, JavaScript, Git, or a public hosting directory. Changing the Google account password revokes its App Passwords; generate and install a replacement if that happens.

## 2. Get the existing Turnstile keys or create a widget

This form also requires Cloudflare Turnstile bot protection. Gmail settings alone will not enable it.

In the [Cloudflare Turnstile dashboard](https://dash.cloudflare.com/?to=/:account/turnstile), reuse the website's existing widget if available. Otherwise select **Add widget**, name it `LAN contact`, authorize `lanehitus.ee` and `www.lanehitus.ee`, choose **Managed**, leave pre-clearance disabled, and select **Create**. Keep the widget's sitekey and secret key privately for the next step. Use real widget keys; the handler rejects published test keys. [Cloudflare widget instructions](https://developers.cloudflare.com/turnstile/get-started/widget-management/dashboard/).

## 3. Generate the private configuration on your laptop

Run in your local terminal:

```sh
cd /Users/pavelpsecuk/Documents/github/lanehitus.ee
python3 website/configure-mail.py
```

Press Enter at the Gmail-address prompt to use `lebjodkin.toll68@gmail.com`. Enter the App Password, Turnstile sitekey, and Turnstile secret when prompted. Password and secret input are hidden. Have all three values ready: this replaces the local `website/.mail-config.json` after input validation. It does not send a test email.

The generated settings are:

| Setting | Value |
| --- | --- |
| SMTP server | `smtp.gmail.com` |
| Port | `465` |
| Security | Implicit TLS, with certificate verification |
| Authentication | Required |
| Username and From | `lebjodkin.toll68@gmail.com` when accepting the default |
| Password | The Gmail App Password |
| To | `lebjodkin.toll68@gmail.com` |

These server/port settings follow [Google's SMTP documentation](https://developers.google.com/workspace/gmail/imap/imap-smtp?hl=en). The Gmail inbox does not need a forwarding rule for this form.

## 4. Install on OVH

An authorized human must perform this live deployment; local changes alone do not repair the hosted form. Follow [DEPLOY-OVH.md](DEPLOY-OVH.md) for backups, runtime requirements, permissions, upload order, and rollback.

For the documented FTP layout:

1. Back up any existing private mail configuration securely, outside public folders.
2. Put the generated file at **`/lanehitus-private/.mail-config.json`**. This folder must be a sibling of public **`/lanehitus`**, outside every website root. It must not be `/lanehitus/website/.mail-config.json` or `/lanehitus/lanehitus-private/`.
3. Give the private directory mode `0700` and configuration mode `0600`, owned by the hosting PHP user. PHP must be able to create/write `/lanehitus-private/.contact-state/`.
4. Ensure the public site has the root **`.htaccess`**, **`.user.ini`**, **`api/index.php`**, and the complete **`api/vendor/phpmailer/`** directory, plus the matching pages and assets from the deployment guide. If those are already installed, this change requires updating `api/index.php` and the private configuration only. The setup script and this guide stay on your laptop.

Do not change account-wide PHP settings or another website's files to repair this form.

## 5. Check configuration, then delivery

Open **`https://lanehitus.ee/api/token`** in your browser. Expect JSON containing `"ready": true`, a nonempty `token`, and `captcha.provider` equal to `"turnstile"`. Do not share the token. This is a configuration check; it does not test Google authentication or Cloudflare connectivity.

If it fails:

| Result | What the operator should check |
| --- | --- |
| 404 or HTML instead of JSON | Install the API, PHPMailer files, and `.htaccess` routes in the actual OVH document root. |
| JSON with `"ready": false` | The private configuration, PHP prerequisites, or mailer files are missing/invalid. |
| HTTP 503 with a generic error | Check private-directory ownership/write permissions and the hosting PHP error log. |

The updated handler logs only fixed configuration-error categories, prefixed `LAN contact unavailable:`. It never logs the configuration values. For example, `configuration_file_unavailable` means the private file is missing, unreadable, or too large; `configuration_fields_missing` means a required SMTP or Turnstile field is absent/empty; `turnstile_keys_invalid` means a key is malformed or a published test key; `smtp_identity_invalid` means a mailbox/host is invalid or From differs from the authenticated user. No diagnostic categories or credentials are returned to website visitors.

An operator with server shell access can also run the following from the deployed public site directory, with the same PHP runtime and user as the website:

```sh
php api/index.php --check-config
```

This reports a safe category and exits nonzero for invalid configuration or unwritable state storage. It does not contact Gmail or Cloudflare, write state, or send messages. A successful result does not validate credentials, existing state contents, or delivery.

Finally, submit one clearly labelled test through the real form, complete Turnstile, and confirm the message arrives in `lebjodkin.toll68@gmail.com` (including Spam if necessary). Check a visitor email's Reply-To or a phone enquiry's callback number. A success response means the SMTP server accepted the message; verify the inbox separately. If configuration passes but sending fails, the operator must check the App Password, widget hostname/keys, and hosting connectivity to Gmail and Cloudflare. Keep all secrets private.
