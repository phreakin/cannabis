<?php
/**
 * api/scripts.php – Script management API
 *
 * GET  ?action=list                       List available .py scripts
 * GET  ?action=read&path=<rel_path>       Read script content
 * POST ?action=save  body:{path,content}  Save (create or overwrite) a script
 * POST ?action=run   body:{path}          Run a script (120s timeout)
 * DELETE ?path=<rel_path>                 Delete a script
 */

require_once __DIR__ . '/../includes/config.php';

header('Content-Type: application/json');

// ── Helpers ────────────────────────────────────────────────────────────────────

function json_ok(mixed $data): never {
    echo json_encode(['ok' => true] + (array)$data);
    exit;
}

function json_err(string $msg, int $code = 400): never {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg]);
    exit;
}

// Allowed directories (relative to APP_ROOT)
const ALLOWED_DIRS = ['scripts', 'src', 'src/collectors', 'src/storage', 'src/utils'];

/**
 * Resolve a relative path like "scripts/foo.py" to an absolute path.
 * Returns false if the path is not within an allowed directory or is traversal.
 */
function resolve_script_path(string $rel): string|false {
    if ($rel === '') return false;

    // Normalise slashes
    $rel = str_replace('\\', '/', $rel);

    // Must end in .py
    if (!preg_match('/\.py$/i', $rel)) return false;

    // Must not contain .. segments
    if (str_contains($rel, '..')) return false;

    // Must start with an allowed directory
    $allowed = false;
    foreach (ALLOWED_DIRS as $ad) {
        if (strpos($rel, $ad . '/') === 0) {
            $allowed = true;
            break;
        }
    }
    if (!$allowed) return false;

    $abs = APP_ROOT . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $rel);

    // For existing files, confirm realpath stays within APP_ROOT
    if (file_exists($abs)) {
        $real = realpath($abs);
        if ($real === false) return false;
        if (strpos($real, realpath(APP_ROOT) . DIRECTORY_SEPARATOR) !== 0) return false;
    }

    return $abs;
}

// ── Router ─────────────────────────────────────────────────────────────────────

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$action = $_GET['action'] ?? '';

// Parse JSON body once
$body = [];
if (in_array($method, ['POST', 'PUT', 'PATCH'], true)) {
    $raw  = file_get_contents('php://input');
    $body = json_decode($raw, true) ?? [];
}

// ── LIST ───────────────────────────────────────────────────────────────────────

if ($method === 'GET' && $action === 'list') {
    $files = [];
    foreach (ALLOWED_DIRS as $rel_dir) {
        $abs_dir = APP_ROOT . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $rel_dir);
        if (!is_dir($abs_dir)) continue;
        foreach (glob($abs_dir . DIRECTORY_SEPARATOR . '*.py') as $path) {
            $files[] = [
                'rel_path' => $rel_dir . '/' . basename($path),
                'dir'      => $rel_dir,
                'filename' => basename($path),
                'size'     => filesize($path),
                'mtime'    => filemtime($path),
            ];
        }
    }
    // Sort by dir then filename
    usort($files, fn($a, $b) => ($a['dir'] <=> $b['dir']) ?: ($a['filename'] <=> $b['filename']));
    json_ok(['files' => $files, 'count' => count($files)]);
}

// ── READ ───────────────────────────────────────────────────────────────────────

if ($method === 'GET' && $action === 'read') {
    $rel = trim($_GET['path'] ?? '');
    $abs = resolve_script_path($rel);
    if ($abs === false) json_err('Invalid or disallowed path.');
    if (!file_exists($abs)) json_err('Script not found.', 404);

    $content = file_get_contents($abs);
    if ($content === false) json_err('Could not read file.', 500);

    json_ok(['path' => $rel, 'content' => $content]);
}

// ── SAVE ───────────────────────────────────────────────────────────────────────

if ($method === 'POST' && $action === 'save') {
    $rel     = trim($body['path'] ?? '');
    $content = $body['content'] ?? '';

    $abs = resolve_script_path($rel);
    if ($abs === false) json_err('Invalid or disallowed path.');

    // Ensure parent directory exists
    $parent = dirname($abs);
    if (!is_dir($parent)) {
        if (!mkdir($parent, 0755, true)) {
            json_err('Could not create directory: ' . dirname($rel), 500);
        }
    }

    // Atomically write via temp file
    $tmp = $abs . '.tmp' . getmypid();
    if (file_put_contents($tmp, $content) === false) {
        json_err('Could not write file.', 500);
    }
    if (!rename($tmp, $abs)) {
        @unlink($tmp);
        json_err('Could not save file (rename failed).', 500);
    }

    json_ok(['message' => 'Script saved.', 'path' => $rel, 'size' => strlen($content)]);
}

// ── RUN ────────────────────────────────────────────────────────────────────────

if ($method === 'POST' && $action === 'run') {
    $rel = trim($body['path'] ?? '');
    $abs = resolve_script_path($rel);
    if ($abs === false) json_err('Invalid or disallowed path.');
    if (!file_exists($abs)) json_err('Script not found.', 404);

    // Find python3 (or python on Windows)
    $python = null;
    foreach (['python3', 'python', '/usr/bin/python3', '/usr/local/bin/python3'] as $candidate) {
        // exec returns empty string if not found
        $test = shell_exec('command -v ' . escapeshellarg($candidate) . ' 2>/dev/null');
        if ($test === null) {
            // On Windows, try where
            $test = shell_exec('where ' . escapeshellarg($candidate) . ' 2>NUL');
        }
        if (!empty(trim((string)$test))) {
            $python = $candidate;
            break;
        }
    }
    if ($python === null) {
        // Last resort: just use 'python3' and let it fail gracefully
        $python = 'python3';
    }

    $timeout     = 120; // seconds
    $project_root = APP_ROOT;

    $descriptors = [
        0 => ['pipe', 'r'],   // stdin
        1 => ['pipe', 'w'],   // stdout
        2 => ['pipe', 'w'],   // stderr
    ];

    $cmd = escapeshellarg($python) . ' ' . escapeshellarg($abs);

    $proc = proc_open($cmd, $descriptors, $pipes, $project_root, null);
    if (!is_resource($proc)) {
        json_err('Could not start process.', 500);
    }

    fclose($pipes[0]); // close stdin

    // Set non-blocking
    stream_set_blocking($pipes[1], false);
    stream_set_blocking($pipes[2], false);

    $output    = '';
    $start     = microtime(true);
    $timed_out = false;

    while (true) {
        $elapsed = microtime(true) - $start;
        if ($elapsed > $timeout) {
            proc_terminate($proc, 9);
            $timed_out = true;
            break;
        }

        $status = proc_get_status($proc);
        $chunk1 = fread($pipes[1], 8192);
        $chunk2 = fread($pipes[2], 8192);
        if ($chunk1) $output .= $chunk1;
        if ($chunk2) $output .= $chunk2;

        if (!$status['running']) break;
        usleep(50000); // 50ms poll
    }

    // Drain remaining output
    $output .= stream_get_contents($pipes[1]);
    $output .= stream_get_contents($pipes[2]);

    fclose($pipes[1]);
    fclose($pipes[2]);

    $exit_code = proc_close($proc);
    if ($timed_out) $exit_code = -1;

    $duration = round(microtime(true) - $start, 2);

    json_ok([
        'output'    => $output,
        'exit_code' => $exit_code,
        'duration'  => $duration,
        'timed_out' => $timed_out,
    ]);
}

// ── DELETE ─────────────────────────────────────────────────────────────────────

if ($method === 'DELETE') {
    $rel = trim($_GET['path'] ?? '');
    $abs = resolve_script_path($rel);
    if ($abs === false) json_err('Invalid or disallowed path.');
    if (!file_exists($abs)) json_err('Script not found.', 404);

    if (!unlink($abs)) {
        json_err('Could not delete file.', 500);
    }

    json_ok(['message' => 'Script deleted.', 'path' => $rel]);
}

// ── Fallback ───────────────────────────────────────────────────────────────────

json_err('Unknown action or method.', 400);
