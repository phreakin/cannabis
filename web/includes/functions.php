<?php
/**
 * functions.php – Shared utility functions.
 */

require_once __DIR__ . '/db.php';

// ── Output helpers ────────────────────────────────────────────────────────────

function h(mixed $v): string {
    return htmlspecialchars((string)($v ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function json_out(mixed $data, int $status = 200): never {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function json_error(string $msg, int $status = 400): never {
    json_out(['error' => $msg], $status);
}

// ── Request helpers ───────────────────────────────────────────────────────────

function get_int(string $key, int $default = 0): int {
    return isset($_GET[$key]) ? (int)$_GET[$key] : $default;
}

function get_str(string $key, string $default = ''): string {
    return isset($_GET[$key]) ? trim((string)$_GET[$key]) : $default;
}

function post_int(string $key, int $default = 0): int {
    return isset($_POST[$key]) ? (int)$_POST[$key] : $default;
}

function post_str(string $key, string $default = ''): string {
    return isset($_POST[$key]) ? trim((string)$_POST[$key]) : $default;
}

function body_json(): array {
    static $body = null;
    if ($body === null) {
        $raw  = file_get_contents('php://input');
        $body = $raw ? (json_decode($raw, true) ?? []) : [];
    }
    return $body;
}

function require_method(string ...$methods): void {
    if (!in_array($_SERVER['REQUEST_METHOD'], $methods, true)) {
        json_error('Method not allowed', 405);
    }
}

// ── Pagination ─────────────────────────────────────────────────────────────────

function paginate(int $total, int $page, int $perPage): array {
    $pages = $perPage > 0 ? (int)ceil($total / $perPage) : 1;
    return [
        'total'    => $total,
        'page'     => $page,
        'per_page' => $perPage,
        'pages'    => max(1, $pages),
    ];
}

function limit_offset(int $page, int $perPage): array {
    $page   = max(1, $page);
    $offset = ($page - 1) * $perPage;
    return [$perPage, $offset];
}

// ── Formatting ────────────────────────────────────────────────────────────────

function fmt_number(int|float|null $n): string {
    return $n !== null ? number_format((float)$n) : '–';
}

function fmt_date(string|null $dt, string $fmt = 'Y-m-d H:i'): string {
    if (!$dt) return '–';
    try {
        return (new DateTimeImmutable($dt))->format($fmt);
    } catch (Exception) {
        return h($dt);
    }
}

function fmt_duration(float|null $secs): string {
    if ($secs === null) return '–';
    if ($secs < 60)  return round($secs, 1) . 's';
    if ($secs < 3600) return round($secs / 60, 1) . 'm';
    return round($secs / 3600, 1) . 'h';
}

function time_ago(string|null $dt): string {
    if (!$dt) return '–';
    try {
        $diff = (new DateTimeImmutable())->getTimestamp() -
                (new DateTimeImmutable($dt))->getTimestamp();
    } catch (Exception) {
        return h($dt);
    }
    if ($diff < 60)     return $diff . 's ago';
    if ($diff < 3600)   return floor($diff / 60) . 'm ago';
    if ($diff < 86400)  return floor($diff / 3600) . 'h ago';
    return floor($diff / 86400) . 'd ago';
}

function status_badge(string|null $status): string {
    $map = [
        'success'  => 'bg-success',
        'failed'   => 'bg-danger',
        'running'  => 'bg-primary',
        'partial'  => 'bg-warning text-dark',
        'skipped'  => 'bg-secondary',
        'pending'  => 'bg-info text-dark',
    ];
    $cls = $map[strtolower((string)$status)] ?? 'bg-secondary';
    return '<span class="badge ' . $cls . '">' . h($status) . '</span>';
}

function format_badge(string|null $fmt): string {
    $map = [
        'soda'    => 'badge-soda',
        'csv'     => 'badge-csv',
        'json'    => 'badge-json',
        'geojson' => 'badge-geojson',
        'xml'     => 'badge-xml',
    ];
    $cls = $map[strtolower((string)$fmt)] ?? 'bg-secondary';
    return '<span class="badge ' . $cls . '">' . h(strtoupper((string)$fmt)) . '</span>';
}

function level_badge(string|null $level): string {
    $map = [
        'DEBUG'   => 'bg-secondary',
        'INFO'    => 'bg-info text-dark',
        'WARNING' => 'bg-warning text-dark',
        'ERROR'   => 'bg-danger',
    ];
    $cls = $map[strtoupper((string)$level)] ?? 'bg-secondary';
    return '<span class="badge ' . $cls . '">' . h($level) . '</span>';
}

// ── Dashboard stats ───────────────────────────────────────────────────────────

function get_dashboard_stats(): array {
    return [
        'total_sources'   => (int)db_val("SELECT COUNT(*) FROM data_sources"),
        'enabled_sources' => (int)db_val("SELECT COUNT(*) FROM data_sources WHERE enabled=1"),
        'total_records'   => (int)db_val("SELECT COUNT(*) FROM raw_records"),
        'gps_records'     => (int)db_val("SELECT COUNT(*) FROM raw_records WHERE latitude IS NOT NULL AND longitude IS NOT NULL"),
        'total_runs'      => (int)db_val("SELECT COUNT(*) FROM collection_runs"),
        'runs_today'      => (int)db_val("SELECT COUNT(*) FROM collection_runs WHERE DATE(started_at)=CURDATE()"),
        'failed_runs'     => (int)db_val("SELECT COUNT(*) FROM collection_runs WHERE status='failed' AND started_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)"),
        'total_schedules' => (int)db_val("SELECT COUNT(*) FROM collection_schedules WHERE enabled=1"),
    ];
}

// ── Drop-down option lists ─────────────────────────────────────────────────────

function get_distinct_states(): array {
    return db_all("SELECT DISTINCT state FROM data_sources WHERE state IS NOT NULL ORDER BY state");
}

function get_distinct_categories(): array {
    return db_all("SELECT DISTINCT category FROM data_sources WHERE category IS NOT NULL ORDER BY category");
}

function get_all_sources(bool $enabled_only = false): array {
    $where = $enabled_only ? 'WHERE enabled=1' : '';
    return db_all("SELECT id, source_id, name, state, category, format, enabled FROM data_sources $where ORDER BY state, name");
}

// ── App settings ──────────────────────────────────────────────────────────────

function get_setting(string $key, mixed $default = null): mixed {
    $row = db_row("SELECT value, value_type FROM app_settings WHERE `key`=?", [$key]);
    if (!$row) return $default;
    return cast_setting($row['value'], $row['value_type']);
}

function set_setting(string $key, mixed $value): void {
    db_exec(
        "INSERT INTO app_settings (`key`, value, updated_at) VALUES (?,?,NOW())
         ON DUPLICATE KEY UPDATE value=VALUES(value), updated_at=NOW()",
        [$key, (string)$value]
    );
}

function cast_setting(string|null $value, string $type): mixed {
    if ($value === null) return null;
    return match($type) {
        'int'   => (int)$value,
        'float' => (float)$value,
        'bool'  => in_array(strtolower($value), ['true','1','yes'], true),
        'json'  => json_decode($value, true),
        default => $value,
    };
}

// ── CSRF (lightweight, stateless token) ──────────────────────────────────────

function csrf_token(): string {
    if (session_status() === PHP_SESSION_NONE) session_start();
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(16));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string {
    return '<input type="hidden" name="_csrf" value="' . h(csrf_token()) . '">';
}

function csrf_verify(): void {
    if (session_status() === PHP_SESSION_NONE) session_start();
    $token = $_POST['_csrf'] ?? ($_SERVER['HTTP_X_CSRF_TOKEN'] ?? '');
    if (!hash_equals($_SESSION['csrf'] ?? '', $token)) {
        json_error('CSRF token mismatch', 403);
    }
}

// ── Redirect ──────────────────────────────────────────────────────────────────

function redirect(string $url): never {
    header('Location: ' . $url);
    exit;
}

function base_url(string $path = ''): string {
    $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
    $host   = $_SERVER['HTTP_HOST'] ?? 'localhost';
    // Detect if we are inside /web/ subfolder
    $script = $_SERVER['SCRIPT_NAME'] ?? '';
    $base   = rtrim(dirname($script), '/\\');
    // Walk up if inside a subdirectory (e.g. /web/api/)
    if (str_ends_with($base, '/api')) $base = dirname($base);
    return $scheme . '://' . $host . $base . '/' . ltrim($path, '/');
}
