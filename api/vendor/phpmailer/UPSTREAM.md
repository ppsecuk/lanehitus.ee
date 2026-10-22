# PHPMailer

Unmodified minimal SMTP files from [PHPMailer v7.1.1](https://github.com/PHPMailer/PHPMailer/releases/tag/v7.1.1), downloaded from that release tag. Licensed under the included LGPL 2.1 license. No Composer installation is required on the host.

SHA-256:

```text
22ab858ae438d98f58f41f38ad2191d1b0d59570aebea0463a7948cfae1021b7  src/Exception.php
45599a196ae7944ee2dcd4f3d3da0ac4243513d346b2d77bbd15dbd0c37f7064  src/PHPMailer.php
522bcf0d07be7e7e00114711db5c9ce2b4d59ac041c5ec36eaadd979d5fa7046  src/SMTP.php
a1a33180d02960ab1c5de36cf20b1a2f0fe9888d83826ad263da5db52f1b183b  LICENSE
```

On updates, replace all three source files and the license together from a reviewed upstream release; update these hashes and run the local SMTP integration tests. This directory is blocked by the site's `.htaccess` and is loaded only by `api/index.php`.
