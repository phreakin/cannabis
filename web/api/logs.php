<?php
/**
 * api/logs.php – Read collection_logs.
 *
 * GET  api/logs.php               – paginated list
 * POST api/logs.php?action=purge  – delete logs older than N days
 */
require_once dirname(__DIR__) . '/includes/functions.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = get_str('action');

// ── Purge ─────────────────────────────────────────────────────────────────────
if ($action === 'purge') {
    require_method('POST');
    $body = body_json();
    $days = max(1, (int)($body['days'] ?? get_int('days', 90)));
    $deleted = (int)db_exec(
        "DELETE FROM collection_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL ? DAY)",
        [$days]
    );
    json_out(['success'=>true, 'deleted'=>$deleted, 'message'=>"Deleted $deleted log entries older than $days days"]);
}

// ── GET list ──────────────────────────────────────────────────────────────────
require_method('GET');

$page     = max(1, get_int('page', 1));
$per_page = min(500, max(1, get_int('per_page', 100)));
$level    = get_str('level');
$src_str  = get_str('source');
$run_id   = get_int('run_id');
$since    = get_str('since');
$q        = get_str('q');

$where = []; $params = [];
if ($level)  { $where[] = 'cl.level = ?';     $params[] = strtoupper($level); }
if ($run_id) { $where[] = 'cl.run_id = ?';    $params[] = $run_id; }
if ($since)  { $where[] = 'cl.timestamp >= ?';$params[] = $since . ' 00:00:00'; }
if ($q)      { $where[] = 'cl.message LIKE ?';$params[] = "%$q%"; }
if ($src_str) {
    $ds = db_row("SELECT id FROM data_sources WHERE source_id=?", [$src_str]);
    if ($ds) { $where[] = 'cl.source_id = ?'; $params[] = $ds['id']; }
}
$wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

$total = (int)db_val("SELECT COUNT(*) FROM collection_logs cl $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);

$rows = db_all("
    SELECT cl.id, cl.level, cl.message, cl.details, cl.timestamp,
           cl.run_id, cl.source_id,
           ds.name AS source_name, ds.source_id AS src_id
    FROM   collection_logs cl
    LEFT   JOIN data_sources ds ON ds.id = cl.source_id
    $wclause
    ORDER  BY cl.timestamp DESC LIMIT ? OFFSET ?",
    array_merge($params, [$limit, $offset]));

foreach ($rows as &$r) {
    $r['details'] = $r['details'] ? json_decode($r['details'], true) : null;
}

json_out(array_merge(paginate($total, $page, $per_page), ['logs' => $rows]));
