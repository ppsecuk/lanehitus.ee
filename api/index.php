<?php
declare(strict_types=1);

// OVH Web Hosting entry point. Configuration and mutable state are outside the site.
ini_set('display_errors', '0');
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

const PRIVATE_DIR = __DIR__ . '/../../lanehitus-private';
const UNAVAILABLE = 'Отправка временно недоступна. Пожалуйста, позвоните нам.';
const INVALID_FORM = 'Проверьте поля и файлы. Максимум 5 файлов, 10 МБ суммарно.';
const UNCONFIRMED = 'Не удалось подтвердить отправку. Пожалуйста, позвоните нам.';
const RETRY = 'Обновите страницу и попробуйте ещё раз.';
const HUMAN_CHECK_FAILED = 'Проверка не пройдена. Повторите проверку и отправку.';
const HUMAN_CHECK_UNAVAILABLE = 'Проверка временно недоступна. Повторите попытку или позвоните нам.';
const MAX_BYTES = 10000000;

function respond(int $status, array $body): never
{
    http_response_code($status);
    echo json_encode($body, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    exit;
}

function mailSettings(): ?array
{
    $path = PRIVATE_DIR . '/.mail-config.json';
    if (!is_file($path) || !is_readable($path) || filesize($path) > 16384
        || !extension_loaded('openssl') || !extension_loaded('fileinfo')
        || !filter_var(ini_get('allow_url_fopen'), FILTER_VALIDATE_BOOL)) {
        return null;
    }
    foreach (['Exception', 'PHPMailer', 'SMTP'] as $source) {
        if (!is_readable(__DIR__ . '/vendor/phpmailer/src/' . $source . '.php')) {
            return null;
        }
    }
    $value = json_decode((string) file_get_contents($path), true);
    if (!is_array($value)) {
        return null;
    }
    foreach (['host', 'user', 'password', 'sender', 'recipient', 'turnstile_site_key', 'turnstile_secret_key'] as $key) {
        if (!isset($value[$key]) || !is_string($value[$key]) || $value[$key] === '') {
            return null;
        }
    }
    foreach (['turnstile_site_key', 'turnstile_secret_key'] as $key) {
        if (!preg_match('/^[A-Za-z0-9_-]{10,100}$/D', $value[$key])
            || preg_match('/^[123]x0{20,}/', $value[$key])) {
            // Cloudflare's published always-pass test keys are not deployment credentials.
            return null;
        }
    }
    if (!filter_var($value['host'], FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME)
        || strlen($value['host']) > 253 || preg_match('/[\r\n\x00]/', $value['user'])
        || !filter_var($value['user'], FILTER_VALIDATE_EMAIL)
        || !filter_var($value['sender'], FILTER_VALIDATE_EMAIL)
        || !filter_var($value['recipient'], FILTER_VALIDATE_EMAIL)
        || strcasecmp($value['sender'], $value['user']) !== 0) {
        return null;
    }
    $port = $value['port'] ?? 465;
    if (!in_array($port, [465, 587, '465', '587'], true)) {
        return null;
    }
    $value['port'] = (int) $port;
    if (isset($value['ca_file']) && (!is_string($value['ca_file']) || !is_readable($value['ca_file']))) {
        return null;
    }
    return $value;
}

function stateDirectory(): string
{
    $path = PRIVATE_DIR . '/.contact-state';
    if (!is_dir($path) && !@mkdir($path, 0700) && !is_dir($path)) {
        throw new RuntimeException('Private state unavailable');
    }
    if (!is_writable($path)) {
        throw new RuntimeException('Private state not writable');
    }
    return $path;
}

function signingSecret(string $directory): string
{
    $path = $directory . '/secret';
    $handle = @fopen($path, 'c+b');
    if ($handle === false || !flock($handle, LOCK_EX)) {
        throw new RuntimeException('Private secret unavailable');
    }
    try {
        @chmod($path, 0600);
        $value = stream_get_contents($handle, 65);
        if ($value === '') {
            $value = bin2hex(random_bytes(32));
            if (fwrite($handle, $value) !== 64 || !fflush($handle)) {
                throw new RuntimeException('Private secret unavailable');
            }
        }
        if (!is_string($value) || !preg_match('/^[a-f0-9]{64}$/D', $value)) {
            throw new RuntimeException('Invalid private secret');
        }
        return $value;
    } finally {
        flock($handle, LOCK_UN);
        fclose($handle);
    }
}

function createToken(string $secret): string
{
    $payload = time() . '.' . bin2hex(random_bytes(16));
    return $payload . '.' . hash_hmac('sha256', $payload, $secret);
}

function validToken(string $value, string $secret): bool
{
    if (!preg_match('/^([0-9]{10})\.([a-f0-9]{32})\.([a-f0-9]{64})$/D', $value, $parts)) {
        return false;
    }
    $age = time() - (int) $parts[1];
    return $age >= 2 && $age <= 3600
        && hash_equals(hash_hmac('sha256', $parts[1] . '.' . $parts[2], $secret), $parts[3]);
}

function field(string $key): string
{
    $value = $_POST[$key] ?? '';
    if (!is_string($value) || strlen($value) > 12000 || !preg_match('//u', $value)
        || str_contains($value, "\0")) {
        throw new InvalidArgumentException(INVALID_FORM);
    }
    return trim($value);
}

function characters(string $value): int
{
    return preg_match_all('/./us', $value);
}

function formFields(): array
{
    $fields = [];
    foreach (['service', 'name', 'contact_method', 'phone', 'email', 'location', 'timing', 'description'] as $key) {
        $fields[$key] = field($key);
    }
    if (!in_array($fields['service'], ['Террасы', 'Гипсокартон', 'Паркет и ламинат', 'Двери', 'Сборка мебели', 'Другая задача'], true)
        || !in_array($fields['location'], ['Tallinn', 'Harjumaa', 'Muu'], true)
        || !in_array($fields['timing'], ['Пока не определился', 'В ближайшее время', 'В течение 1–3 месяцев', 'Позже'], true)
        || characters($fields['name']) > 100
        || characters($fields['description']) < 1 || characters($fields['description']) > 2500) {
        throw new InvalidArgumentException(INVALID_FORM);
    }
    if ($fields['contact_method'] === 'По email') {
        if (strlen($fields['email']) > 254 || !filter_var($fields['email'], FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException(INVALID_FORM);
        }
        unset($fields['phone']);
    } elseif ($fields['contact_method'] === 'По телефону') {
        if (!preg_match('/^[+0-9 ()-]{5,40}$/D', $fields['phone']) || !preg_match('/[0-9]/', $fields['phone'])) {
            throw new InvalidArgumentException(INVALID_FORM);
        }
        unset($fields['email']);
    } else {
        throw new InvalidArgumentException(INVALID_FORM);
    }
    return $fields;
}

function attachments(): array
{
    if (count($_FILES) > 5) {
        throw new InvalidArgumentException(INVALID_FORM);
    }
    $result = [];
    $total = 0;
    $detector = new finfo(FILEINFO_MIME_TYPE);
    $types = ['jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png',
        'webp' => 'image/webp', 'heic' => 'image/heic', 'heif' => 'image/heif', 'pdf' => 'application/pdf'];
    foreach ($_FILES as $key => $file) {
        if (!preg_match('/^attachment[1-5]$/D', (string) $key) || !is_array($file)
            || !isset($file['error'], $file['name'], $file['tmp_name'], $file['size'])
            || $file['error'] !== UPLOAD_ERR_OK || !is_string($file['name'])
            || !is_string($file['tmp_name']) || !is_uploaded_file($file['tmp_name'])) {
            throw new InvalidArgumentException(INVALID_FORM);
        }
        $size = filesize($file['tmp_name']);
        if ($size === false || $size < 1 || ($total += $size) > MAX_BYTES) {
            throw new InvalidArgumentException(INVALID_FORM);
        }
        $name = basename(str_replace('\\', '/', $file['name']));
        $extension = strtolower(pathinfo($name, PATHINFO_EXTENSION));
        if (!isset($types[$extension]) || strlen($name) > 240 || !preg_match('//u', $name)
            || preg_match('/[\x00-\x1f\x7f]/', $name)) {
            throw new InvalidArgumentException(INVALID_FORM);
        }
        $mime = $detector->file($file['tmp_name']);
        $expected = $types[$extension];
        // libmagic varies between hosts for HEIF brands; inspect the ISO-BMFF brand too.
        if (in_array($extension, ['heic', 'heif'], true)) {
            $head = (string) file_get_contents($file['tmp_name'], false, null, 0, 64);
            $brands = str_split(substr($head, 8), 4);
            if (substr($head, 4, 4) !== 'ftyp'
                || !array_intersect($brands, ['heic', 'heix', 'hevc', 'hevx', 'heim', 'heis', 'mif1', 'msf1'])) {
                throw new InvalidArgumentException(INVALID_FORM);
            }
        } elseif ($mime !== $expected) {
            throw new InvalidArgumentException(INVALID_FORM);
        }
        $result[] = ['path' => $file['tmp_name'], 'name' => $name, 'mime' => $expected];
    }
    return $result;
}

function rateLimit(string $directory, string $secret): void
{
    // REMOTE_ADDR is supplied by the host; do not trust visitor-controlled forwarding headers.
    $key = hash_hmac('sha256', $_SERVER['REMOTE_ADDR'] ?? '', $secret);
    $path = $directory . '/rates.json';
    $handle = @fopen($path, 'c+b');
    if ($handle === false || !flock($handle, LOCK_EX)) {
        throw new RuntimeException('Rate state unavailable');
    }
    try {
        @chmod($path, 0600);
        $raw = stream_get_contents($handle, 1000001);
        $rates = $raw === '' ? [] : json_decode((string) $raw, true);
        if (!is_array($rates) || strlen((string) $raw) > 1000000) {
            throw new RuntimeException('Invalid rate state');
        }
        $now = time();
        foreach ($rates as $client => $times) {
            $rates[$client] = array_values(array_filter($times, static fn($stamp) => is_int($stamp) && $stamp > $now - 600));
            if ($rates[$client] === []) {
                unset($rates[$client]);
            }
        }
        $recent = $rates[$key] ?? [];
        if (count($recent) >= 3 || (!isset($rates[$key]) && count($rates) >= 4096)) {
            header('Retry-After: 600');
            respond(429, ['error' => 'Слишком много попыток. Попробуйте через 10 минут.']);
        }
        $rates[$key] = [...$recent, $now];
        $data = json_encode($rates, JSON_THROW_ON_ERROR);
        rewind($handle);
        if (!ftruncate($handle, 0) || fwrite($handle, $data) !== strlen($data) || !fflush($handle)) {
            throw new RuntimeException('Rate state unavailable');
        }
    } finally {
        flock($handle, LOCK_UN);
        fclose($handle);
    }
}

function sendSlot(string $directory)
{
    for ($index = 0; $index < 2; $index++) {
        $path = $directory . '/send-' . $index;
        $handle = @fopen($path, 'c+b');
        if ($handle !== false) {
            @chmod($path, 0600);
            if (flock($handle, LOCK_EX | LOCK_NB)) {
                return $handle;
            }
            fclose($handle);
        }
    }
    header('Retry-After: 10');
    respond(429, ['error' => 'Повторите отправку чуть позже.']);
}

function sendEnquiry(array $fields, array $files, array $settings): void
{
    require_once __DIR__ . '/vendor/phpmailer/src/Exception.php';
    require_once __DIR__ . '/vendor/phpmailer/src/PHPMailer.php';
    require_once __DIR__ . '/vendor/phpmailer/src/SMTP.php';
    $mail = new PHPMailer\PHPMailer\PHPMailer(true);
    $mail->isSMTP();
    $mail->Host = $settings['host'];
    $mail->Port = $settings['port'];
    $mail->SMTPAuth = true;
    $mail->Username = $settings['user'];
    $mail->Password = $settings['password'];
    $mail->SMTPSecure = $settings['port'] === 465
        ? PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_SMTPS
        : PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_STARTTLS;
    $mail->SMTPDebug = 0;
    $mail->Timeout = 15;
    $mail->Timelimit = 20;
    $mail->CharSet = 'UTF-8';
    $mail->SMTPOptions = ['ssl' => ['verify_peer' => true, 'verify_peer_name' => true, 'allow_self_signed' => false]];
    if (isset($settings['ca_file'])) {
        $mail->SMTPOptions['ssl']['cafile'] = $settings['ca_file'];
    }
    $mail->setFrom($settings['sender'], 'LAN Ehitus');
    $mail->addAddress($settings['recipient']);
    if ($fields['contact_method'] === 'По email') {
        $mail->addReplyTo($fields['email']);
    }
    $mail->Subject = 'Новая заявка LAN OÜ — ' . $fields['service'];
    $labels = ['Услуга' => 'service', 'Имя' => 'name', 'Способ связи' => 'contact_method',
        'Телефон' => 'phone', 'Email' => 'email', 'Местоположение' => 'location',
        'Когда начать' => 'timing', 'Описание' => 'description'];
    $parts = [];
    foreach ($labels as $label => $key) {
        if (isset($fields[$key]) && $fields[$key] !== '') {
            $parts[] = $label . ': ' . $fields[$key];
        }
    }
    $mail->Body = implode("\n\n", $parts);
    foreach ($files as $file) {
        $mail->addAttachment($file['path'], $file['name'], 'base64', $file['mime']);
    }
    if (!$mail->send()) {
        throw new RuntimeException('SMTP acceptance not confirmed');
    }
}

function verifyHuman(array $settings): void
{
    $token = field('cf-turnstile-response');
    if ($token === '' || strlen($token) > 2048) {
        respond(403, ['error' => HUMAN_CHECK_FAILED]);
    }
    $data = http_build_query(['secret' => $settings['turnstile_secret_key'], 'response' => $token]);
    $ssl = ['verify_peer' => true, 'verify_peer_name' => true, 'allow_self_signed' => false,
        'peer_name' => 'challenges.cloudflare.com'];
    if (isset($settings['ca_file'])) {
        $ssl['cafile'] = $settings['ca_file'];
    }
    $context = stream_context_create([
        'http' => ['method' => 'POST', 'header' => "Content-Type: application/x-www-form-urlencoded\r\nAccept: application/json\r\n",
            'content' => $data, 'timeout' => 8, 'follow_location' => 0, 'max_redirects' => 0,
            'ignore_errors' => true, 'protocol_version' => 1.1],
        'ssl' => $ssl,
    ]);
    // Fixed endpoint, verified TLS, no redirects, and no enquiry content sent to the provider.
    $connection = @fopen('https://challenges.cloudflare.com/turnstile/v0/siteverify', 'rb', false, $context);
    if ($connection === false) {
        respond(503, ['error' => HUMAN_CHECK_UNAVAILABLE]);
    }
    try {
        $body = @stream_get_contents($connection, 8193);
        $metadata = stream_get_meta_data($connection);
    } finally {
        fclose($connection);
    }
    $headers = $metadata['wrapper_data'] ?? [];
    if (!is_string($body) || strlen($body) > 8192 || ($metadata['timed_out'] ?? true)
        || !preg_match('/^HTTP\/\S+\s+200(?:\s|$)/', $headers[0] ?? '')) {
        respond(503, ['error' => HUMAN_CHECK_UNAVAILABLE]);
    }
    $result = json_decode($body, true);
    if (!is_array($result) || !isset($result['success']) || !is_bool($result['success'])) {
        respond(503, ['error' => HUMAN_CHECK_UNAVAILABLE]);
    }
    if ($result['success'] !== true) {
        $codes = $result['error-codes'] ?? [];
        if (is_array($codes) && array_intersect($codes, ['invalid-input-secret', 'missing-input-secret', 'internal-error'])) {
            respond(503, ['error' => HUMAN_CHECK_UNAVAILABLE]);
        }
        respond(403, ['error' => HUMAN_CHECK_FAILED]);
    }
    if (!in_array($result['hostname'] ?? '', ['lanehitus.ee', 'www.lanehitus.ee'], true)
        || ($result['action'] ?? '') !== 'contact') {
        respond(403, ['error' => HUMAN_CHECK_FAILED]);
    }
}

try {
    $path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH);
    if (!in_array($path, ['/api/token', '/api/enquiry'], true)) {
        respond(404, ['error' => 'Не найдено.']);
    }
    $method = $_SERVER['REQUEST_METHOD'] ?? '';
    if ($method !== ($path === '/api/token' ? 'GET' : 'POST')) {
        header('Allow: ' . ($path === '/api/token' ? 'GET' : 'POST'));
        respond(405, ['error' => RETRY]);
    }
    $settings = mailSettings();
    if ($path === '/api/token') {
        if ($settings === null) {
            respond(200, ['ready' => false, 'token' => '']);
        }
        $secret = signingSecret(stateDirectory());
        respond(200, ['ready' => true, 'token' => createToken($secret), 'expiresIn' => 3600, 'minDelayMs' => 2000,
            'captcha' => ['provider' => 'turnstile', 'siteKey' => $settings['turnstile_site_key'], 'action' => 'contact']]);
    }
    if (!in_array($_SERVER['HTTP_ORIGIN'] ?? '', ['https://lanehitus.ee', 'https://www.lanehitus.ee'], true)) {
        respond(403, ['error' => 'Обновите страницу и повторите отправку.']);
    }
    if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > MAX_BYTES + 100000) {
        respond(413, ['error' => INVALID_FORM]);
    }
    if (!str_starts_with(strtolower($_SERVER['CONTENT_TYPE'] ?? ''), 'multipart/form-data;')) {
        respond(400, ['error' => INVALID_FORM]);
    }
    if ($settings === null) {
        respond(503, ['error' => UNAVAILABLE]);
    }
    $directory = stateDirectory();
    $secret = signingSecret($directory);
    if (field('_honey') !== '' || !validToken(field('_token'), $secret)) {
        respond(400, ['error' => RETRY]);
    }
    $fields = formFields();
    $files = attachments();
    rateLimit($directory, $secret);
    $slot = sendSlot($directory);
    try {
        verifyHuman($settings);
        try {
            sendEnquiry($fields, $files, $settings);
        } catch (Throwable $error) {
            // Do not expose SMTP diagnostics, visitor content or account details.
            respond(502, ['error' => UNCONFIRMED]);
        }
    } finally {
        flock($slot, LOCK_UN);
        fclose($slot);
    }
    respond(200, ['ok' => true]);
} catch (InvalidArgumentException $error) {
    respond(400, ['error' => INVALID_FORM]);
} catch (Throwable $error) {
    respond(503, ['error' => UNAVAILABLE]);
}
