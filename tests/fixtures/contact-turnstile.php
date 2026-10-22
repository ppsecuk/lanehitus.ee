<?php
// Disposable local HTTPS provider fixture. Never connects to Cloudflare.
declare(strict_types=1);

$private = '/var/www/lanehitus-private';
$context = stream_context_create(['ssl' => [
    'local_cert' => $private . '/captcha-cert.pem',
    'local_pk' => $private . '/captcha-key.pem',
]]);
$server = stream_socket_server('tls://127.0.0.1:443', $errno, $error,
    STREAM_SERVER_BIND | STREAM_SERVER_LISTEN, $context);
if ($server === false) {
    fwrite(STDERR, "Synthetic captcha fixture failed to start.\n");
    exit(1);
}
file_put_contents($private . '/captcha-ready', 'ready');

while (true) {
    $client = @stream_socket_accept($server, 2);
    if ($client === false) {
        continue;
    }
    stream_set_timeout($client, 10);
    $request = rtrim((string) fgets($client), "\r\n");
    $headers = [];
    while (($line = fgets($client)) !== false && rtrim($line, "\r\n") !== '') {
        if (str_contains($line, ':')) {
            [$key, $value] = explode(':', $line, 2);
            $headers[strtolower(trim($key))] = trim($value);
        }
    }
    $length = (int) ($headers['content-length'] ?? 0);
    $body = '';
    if ($length > 0 && $length <= 4096) {
        while (strlen($body) < $length && !feof($client)) {
            $chunk = fread($client, $length - strlen($body));
            if ($chunk === false || $chunk === '') {
                break;
            }
            $body .= $chunk;
        }
    }
    $fields = [];
    parse_str($body, $fields);
    $token = is_string($fields['response'] ?? null) ? $fields['response'] : '';
    $validSecret = is_string($fields['secret'] ?? null)
        && hash_equals('synthetic-turnstile-secret', $fields['secret']);
    file_put_contents($private . '/captcha-requests.jsonl', json_encode([
        'request' => $request,
        'host' => $headers['host'] ?? '',
        'response' => $token,
        'validSecret' => $validSecret,
        'includesRemoteIP' => array_key_exists('remoteip', $fields),
    ]) . "\n", FILE_APPEND | LOCK_EX);

    $status = '200 OK';
    $result = ['success' => true, 'hostname' => 'lanehitus.ee', 'action' => 'contact'];
    if (!preg_match('#^POST /turnstile/v0/siteverify HTTP/1\.[01]$#D', $request)
        || ($headers['host'] ?? '') !== 'challenges.cloudflare.com'
        || !str_starts_with($headers['content-type'] ?? '', 'application/x-www-form-urlencoded')) {
        $status = '400 Bad Request';
        $result = ['success' => false];
    } elseif (!$validSecret) {
        $result = ['success' => false, 'error-codes' => ['invalid-input-secret']];
    } elseif (!preg_match('/^fixture-valid-[a-f0-9]{32}$/D', $token)) {
        $result = ['success' => false, 'error-codes' => [
            str_starts_with($token, 'fixture-expired-') ? 'timeout-or-duplicate' : 'invalid-input-response',
        ]];
    } else {
        $consumed = json_decode((string) @file_get_contents($private . '/captcha-consumed.json'), true) ?? [];
        if (isset($consumed[$token])) {
            $result = ['success' => false, 'error-codes' => ['timeout-or-duplicate']];
        } else {
            $consumed[$token] = true;
            file_put_contents($private . '/captcha-consumed.json', json_encode($consumed));
        }
    }
    $mode = trim((string) @file_get_contents($private . '/captcha-mode'));
    if ($mode === 'wrong-hostname') {
        $result['hostname'] = 'attacker.example';
    } elseif ($mode === 'wrong-action') {
        $result['action'] = 'unrelated';
    } elseif ($mode === 'http-failure') {
        $status = '500 Internal Server Error';
        $result = ['success' => false];
    } elseif ($mode === 'invalid-success') {
        $result['success'] = 'true';
    }
    $response = $mode === 'bad-json' ? 'synthetic malformed provider JSON' : json_encode($result);
    fwrite($client, "HTTP/1.1 {$status}\r\nContent-Type: application/json\r\nContent-Length: "
        . strlen($response) . "\r\nConnection: close\r\n\r\n" . $response);
    fclose($client);
}
