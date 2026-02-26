<?php
/**
 * db.php – PDO connection singleton.
 * Usage:  $pdo = db();
 */

require_once __DIR__ . '/config.php';

function db(): PDO {
    static $pdo = null;
    if ($pdo !== null) return $pdo;

    $dsn = sprintf(
        'mysql:host=%s;port=%s;dbname=%s;charset=%s',
        DB_HOST, DB_PORT, DB_NAME, DB_CHARSET
    );
    $opts = [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ];
    try {
        $pdo = new PDO($dsn, DB_USER, DB_PASS, $opts);
    } catch (PDOException $e) {
        http_response_code(500);
        die(json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]));
    }
    return $pdo;
}

/**
 * Quick scalar fetch helper.
 * e.g. $count = db_val("SELECT COUNT(*) FROM data_sources WHERE enabled=1");
 */
function db_val(string $sql, array $params = []): mixed {
    $st = db()->prepare($sql);
    $st->execute($params);
    $v = $st->fetchColumn();
    return $v === false ? null : $v;
}

/**
 * Fetch a single row.
 */
function db_row(string $sql, array $params = []): ?array {
    $st = db()->prepare($sql);
    $st->execute($params);
    $r = $st->fetch();
    return $r ?: null;
}

/**
 * Fetch all rows.
 */
function db_all(string $sql, array $params = []): array {
    $st = db()->prepare($sql);
    $st->execute($params);
    return $st->fetchAll();
}

/**
 * Execute a statement (INSERT / UPDATE / DELETE).
 * Returns lastInsertId for INSERT, rowCount otherwise.
 */
function db_exec(string $sql, array $params = []): int|string {
    $pdo = db();
    $st  = $pdo->prepare($sql);
    $st->execute($params);
    $isInsert = stripos(ltrim($sql), 'INSERT') === 0;
    return $isInsert ? $pdo->lastInsertId() : $st->rowCount();
}
