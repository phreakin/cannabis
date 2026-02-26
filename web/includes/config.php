<?php
/**
 * config.php – Database and application configuration.
 * Reads from .env file in project root, then falls back to constants below.
 */

// ── Load .env if present ─────────────────────────────────────────────────────
$envFile = dirname(__DIR__, 2) . '/.env';
if (file_exists($envFile)) {
    foreach (file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') continue;
        if (strpos($line, '=') === false) continue;
        [$k, $v] = explode('=', $line, 2);
        $k = trim($k);
        $v = trim($v, " \t\"'");
        if (!array_key_exists($k, $_ENV)) {
            $_ENV[$k] = $v;
            putenv("$k=$v");
        }
    }
}

// ── Database ──────────────────────────────────────────────────────────────────
define('DB_HOST',    $_ENV['MYSQL_HOST']     ?? 'localhost');
define('DB_PORT',    $_ENV['MYSQL_PORT']     ?? '3306');
define('DB_NAME',    $_ENV['MYSQL_DATABASE'] ?? 'cannabis_data');
define('DB_USER',    $_ENV['MYSQL_USER']     ?? 'root');
define('DB_PASS',    $_ENV['MYSQL_PASSWORD'] ?? '');
define('DB_CHARSET', 'utf8mb4');

// ── Application ───────────────────────────────────────────────────────────────
define('APP_NAME',    'Cannabis Data Aggregator');
define('APP_VERSION', '1.0.0');
define('APP_ROOT',    dirname(__DIR__, 2));   // Z:/cannabis-data-aggregator

// ── Web base URL path ──────────────────────────────────────────────────────────
// Auto-detects the URL prefix up to and including /web/ so all links work
// regardless of how deeply the app is nested under the server root.
// e.g.  /cannabis-data-aggregator/web/   or   /web/   or   /
$_s = $_SERVER['SCRIPT_NAME'] ?? '/index.php';
$_p = strpos($_s, '/web/');
define('WEB_BASE', $_p !== false
    ? substr($_s, 0, $_p + 5)          // e.g. /cannabis-data-aggregator/web/
    : rtrim(dirname($_s), '/') . '/'   // fallback for non-standard layouts
);
unset($_s, $_p);

// ── Per-page defaults ─────────────────────────────────────────────────────────
define('DEFAULT_PAGE_SIZE', 50);
define('MAX_EXPORT_ROWS',   100000);
