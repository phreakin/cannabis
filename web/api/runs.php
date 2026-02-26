<?php
/**
 * api/runs.php – Read collection_runs.
 *
 * GET  api/runs.php                   – paginated list
 * GET  api/runs.php?id=N              – single run
 * POST api/runs.php?action=purge      – delete runs older than N days
 */
require_once dirname(__DIR__) . '/includes/functions.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = get_str('action');
$id     = get_int('id');

// ── Purge ─────────────────────────────────────────────────────────────────────
if ($action === 'purge') {
    require_method('POST');
    $body    = body_json();
    $days    = max(1, (int)($body['days'] ?? get_int('days', 180)));
    $deleted = (int)db_exec(
        "DELETE FROM collection_runs WHERE started_at < DATE_SUB(NOW(), INTERVAL ? DAY)",
        [$days]
    );
    json_out(['success'=>true, 'deleted'=>$deleted, 'message'=>"Deleted $deleted runs older than $days days"]);
}

require_method('GET');

// ── Single run ────────────────────────────────────────────────────────────────
if ($id) {
    $run = db_row("
        SELECT cr.*, ds.name AS source_name, ds.source_id AS src_id
        FROM   collection_runs cr
        JOIN   data_sources ds ON ds.id = cr.source_id
        WHERE  cr.id=?", [$id]);
    if (!$run) json_error('Run not found', 404);

    $logs = db_all("
        SELECT id, level, message, timestamp
        FROM   collection_logs
        WHERE  run_id=?
        ORDER  BY timestamp LIMIT 500", [$id]);

    json_out(['run' => $run, 'logs' => $logs]);
}

// ── Paginated list ────────────────────────────────────────────────────────────
$page     = max(1, get_int('page', 1));
$per_page = min(200, max(1, get_int('per_page', 50)));
$status   = get_str('status');
$src_str  = get_str('source');
$since    = get_str('since');

$where = []; $params = [];
if ($status)  { $where[] = 'cr.status = ?';     $params[] = $status; }
if ($since)   { $where[] = 'cr.started_at >= ?';$params[] = $since . ' 00:00:00'; }
if ($src_str) {
    $ds = db_row("SELECT id FROM data_sources WHERE source_id=?", [$src_str]);
    if ($ds) { $where[] = 'cr.source_id = ?'; $params[] = $ds['id']; }
}
$wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

$total = (int)db_val("SELECT COUNT(*) FROM collection_runs cr $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);

$rows = db_all("
    SELECT cr.id, cr.started_at, cr.completed_at, cr.status,
           cr.records_fetched, cr.records_stored, cr.records_updated, cr.records_skipped,
           cr.duration_seconds, cr.triggered_by, cr.error_message,
           ds.name AS source_name, ds.source_id AS src_id, ds.state
    FROM   collection_runs cr
    JOIN   data_sources ds ON ds.id = cr.source_id
    $wclause
    ORDER  BY cr.started_at DESC LIMIT ? OFFSET ?",
    array_merge($params, [$limit, $offset]));

json_out(array_merge(paginate($total, $page, $per_page), ['runs' => $rows]));
