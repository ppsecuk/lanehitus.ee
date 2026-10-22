<?php
// Isolated integration fixture: accepts synthetic mail on container loopback only.
declare(strict_types=1);

$private = '/var/www/lanehitus-private';
$context = stream_context_create(['ssl' => [
    'local_cert' => $private . '/smtp-cert.pem',
    'local_pk' => $private . '/smtp-key.pem',
]]);
$server = stream_socket_server('tls://127.0.0.1:465', $errno, $error,
    STREAM_SERVER_BIND | STREAM_SERVER_LISTEN, $context);
if ($server === false) {
    fwrite(STDERR, "Synthetic SMTP fixture failed to start.\n");
    exit(1);
}
file_put_contents($private . '/smtp-ready', 'ready');

$validPlain = static fn(string $value): bool =>
    hash_equals("\0test@example.test\0test-only", (string) base64_decode($value, true));

while (true) {
    $client = @stream_socket_accept($server, 2);
    if ($client === false) {
        continue;
    }
    stream_set_timeout($client, 10);
    fwrite($client, "220 mail.test ESMTP synthetic fixture\r\n");
    $authStep = 0;
    $authUser = '';
    $authenticated = false;
    $message = '';
    $data = false;
    $envelope = ['from' => '', 'to' => [], 'message' => ''];
    while (($line = fgets($client)) !== false) {
        $command = rtrim($line, "\r\n");
        if ($data) {
            if ($command === '.') {
                $envelope['message'] = $message;
                file_put_contents($private . '/smtp-messages.jsonl',
                    json_encode($envelope, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
                fwrite($client, "250 2.0.0 Synthetic message accepted\r\n");
                $data = false;
            } else {
                $message .= (str_starts_with($line, '..') ? substr($line, 1) : $line);
            }
            continue;
        }
        if ($authStep === 1) {
            $authUser = (string) base64_decode($command, true);
            $authStep = 2;
            fwrite($client, "334 UGFzc3dvcmQ6\r\n");
        } elseif ($authStep === 2) {
            $authStep = 0;
            $authenticated = hash_equals('test@example.test', $authUser)
                && hash_equals('test-only', (string) base64_decode($command, true));
            fwrite($client, $authenticated ? "235 2.7.0 Synthetic authentication accepted\r\n"
                : "535 5.7.8 Synthetic authentication rejected\r\n");
        } elseif ($authStep === 3) {
            $authStep = 0;
            $authenticated = $validPlain($command);
            fwrite($client, $authenticated ? "235 2.7.0 Synthetic authentication accepted\r\n"
                : "535 5.7.8 Synthetic authentication rejected\r\n");
        } elseif (preg_match('/^(EHLO|HELO) /i', $command)) {
            fwrite($client, "250-mail.test\r\n250-AUTH LOGIN PLAIN\r\n250 SIZE 20000000\r\n");
        } elseif (strcasecmp($command, 'AUTH LOGIN') === 0) {
            $authStep = 1;
            fwrite($client, "334 VXNlcm5hbWU6\r\n");
        } elseif (preg_match('/^AUTH PLAIN(?: (.*))?$/i', $command, $matches)) {
            if (!isset($matches[1]) || $matches[1] === '') {
                $authStep = 3;
                fwrite($client, "334 \r\n");
            } else {
                $authenticated = $validPlain($matches[1]);
                fwrite($client, $authenticated ? "235 2.7.0 Synthetic authentication accepted\r\n"
                    : "535 5.7.8 Synthetic authentication rejected\r\n");
            }
        } elseif (preg_match('/^MAIL FROM:\s*<([^>]+)>/i', $command, $matches)) {
            if (!$authenticated) {
                fwrite($client, "530 5.7.0 Authentication required\r\n");
            } else {
                $envelope['from'] = $matches[1];
                fwrite($client, "250 2.1.0 Sender accepted\r\n");
            }
        } elseif (preg_match('/^RCPT TO:\s*<([^>]+)>/i', $command, $matches)) {
            $envelope['to'][] = $matches[1];
            fwrite($client, "250 2.1.5 Recipient accepted\r\n");
        } elseif (strcasecmp($command, 'DATA') === 0) {
            $mode = @file_get_contents($private . '/smtp-mode');
            if (trim((string) $mode) === 'reject') {
                fwrite($client, "451 4.3.0 Synthetic backend failure test-only\r\n");
            } else {
                $data = true;
                fwrite($client, "354 End synthetic data with dot\r\n");
            }
        } elseif (strcasecmp($command, 'QUIT') === 0) {
            fwrite($client, "221 2.0.0 Bye\r\n");
            break;
        } elseif (strcasecmp($command, 'RSET') === 0) {
            $envelope = ['from' => '', 'to' => [], 'message' => ''];
            $message = '';
            fwrite($client, "250 2.0.0 Reset\r\n");
        } else {
            fwrite($client, "250 2.0.0 OK\r\n");
        }
    }
    fclose($client);
}
