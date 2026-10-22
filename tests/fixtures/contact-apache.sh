#!/bin/sh
# Runs only in a disposable local integration container, never on OVH.
set -eu
chown -R www-data:www-data /var/www/lanehitus-private
chmod 700 /var/www/lanehitus-private
printf '%s\n' \
  '<Directory /var/www/html>' \
  '  AllowOverride All' \
  '  Require all granted' \
  '</Directory>' \
  'ServerName lanehitus.ee' \
  'SetEnvIf Request_URI "^" HTTPS=on' \
  > /etc/apache2/conf-enabled/contact-test.conf
printf '%s\n' \
  'post_max_size=12M' \
  'upload_max_filesize=10M' \
  'max_file_uploads=20' \
  'max_execution_time=60' \
  'display_errors=Off' \
  'log_errors=On' \
  > /usr/local/etc/php/conf.d/contact-test.ini
a2enmod rewrite headers >/dev/null
php /contact-fixtures/contact-smtp.php &
php /contact-fixtures/contact-turnstile.php &
exec apache2-foreground
