<?php
/**
 * api/schedules.php – CRUD for collection_schedules.
 *
 * GET    api/schedules.php              – list schedules
 * GET    api/schedules.php?id=N         – single schedule
 * POST   api/schedules.php              – create (JSON body)
 * PUT    api/schedules.php?id=N         – update (JSON body)
 * DELETE api/schedules.php?id=N         – delete
 * POST   api/schedules.php?action=enable&id=SCHED_ID
 * POST   api/schedules.php?action=disable&id=SCHED_ID
 */
require_once dirname(__DIR__) . '/includes/functions.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = get_str('action');
$id_raw = get_str('id');

function resolve_schedule(string $id_raw): ?array {
    if (ctype_digit($id_raw)) {
        return db_row("SELECT cs.*, ds.name AS source_name, ds.source_id AS src_id
                       FROM collection_schedules cs JOIN data_sources ds ON ds.id=cs.source_id
                       WHERE cs.id=?", [(int)$id_raw]);
    }
    return db_row("SELECT cs.*, ds.name AS source_name, ds.source_id AS src_id
                   FROM collection_schedules cs JOIN data_sources ds ON ds.id=cs.source_id
                   WHERE cs.schedule_id=?", [$id_raw]);
}

// Actions
if ($action) {
    require_method('POST');
    $sch = resolve_schedule($id_raw);
    if (!$sch) json_error('Schedule not found', 404);
    if ($action === 'enable')  { db_exec("UPDATE collection_schedules SET enabled=1, updated_at=NOW() WHERE id=?", [$sch['id']]); json_out(['success'=>true]); }
    if ($action === 'disable') { db_exec("UPDATE collection_schedules SET enabled=0, updated_at=NOW() WHERE id=?", [$sch['id']]); json_out(['success'=>true]); }
    json_error('Unknown action', 400);
}

// GET single
if ($method === 'GET' && $id_raw !== '') {
    $sch = resolve_schedule($id_raw);
    if (!$sch) json_error('Schedule not found', 404);
    $sch['run_count'] = (int)db_val("SELECT COUNT(*) FROM collection_runs WHERE schedule_id=?", [$sch['id']]);
    json_out(['schedule' => $sch]);
}

// GET list
if ($method === 'GET') {
    $page     = max(1, get_int('page', 1));
    $per_page = min(200, max(1, get_int('per_page', 100)));
    $enabled  = get_str('enabled');
    $src_str  = get_str('source');

    $where = []; $params = [];
    if ($enabled === '1') $where[] = 'cs.enabled = 1';
    if ($enabled === '0') $where[] = 'cs.enabled = 0';
    if ($src_str) {
        $ds = db_row("SELECT id FROM data_sources WHERE source_id=?", [$src_str]);
        if ($ds) { $where[] = 'cs.source_id = ?'; $params[] = $ds['id']; }
    }
    $wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';
    $total   = (int)db_val("SELECT COUNT(*) FROM collection_schedules cs $wclause", $params);
    [$limit, $offset] = limit_offset($page, $per_page);

    $rows = db_all("
        SELECT cs.id, cs.schedule_id, cs.name, cs.schedule_type, cs.enabled, cs.priority,
               cs.cron_minute, cs.cron_hour, cs.cron_day_of_month, cs.cron_month, cs.cron_day_of_week,
               cs.interval_value, cs.interval_unit, cs.next_run, cs.last_run, cs.created_at,
               ds.name AS source_name, ds.source_id AS src_id, ds.state
        FROM   collection_schedules cs
        JOIN   data_sources ds ON ds.id = cs.source_id
        $wclause
        ORDER  BY cs.enabled DESC, ds.state, ds.name
        LIMIT  ? OFFSET ?", array_merge($params, [$limit, $offset]));

    json_out(array_merge(paginate($total, $page, $per_page), ['schedules' => $rows]));
}

// POST (create)
if ($method === 'POST') {
    $body = body_json();
    if (empty($body['schedule_id']) || empty($body['name']) || empty($body['source_id'])) {
        json_error('schedule_id, name and source_id are required');
    }
    $ds = db_row("SELECT id FROM data_sources WHERE source_id=?", [$body['source_id']]);
    if (!$ds) json_error('Source not found', 404);

    $type = $body['schedule_type'] ?? 'interval';
    $data = [
        'schedule_id'      => $body['schedule_id'],
        'source_id'        => $ds['id'],
        'name'             => $body['name'],
        'schedule_type'    => $type,
        'enabled'          => (int)($body['enabled'] ?? 1),
        'priority'         => (int)($body['priority'] ?? 2),
        'notes'            => $body['notes'] ?? null,
        'cron_minute'      => $body['cron_minute'] ?? '0',
        'cron_hour'        => $body['cron_hour'] ?? '0',
        'cron_day_of_month'=> $body['cron_day_of_month'] ?? '*',
        'cron_month'       => $body['cron_month'] ?? '*',
        'cron_day_of_week' => $body['cron_day_of_week'] ?? '*',
        'interval_value'   => $body['interval_value'] ?? null,
        'interval_unit'    => $body['interval_unit'] ?? null,
    ];
    $cols = implode(', ', array_keys($data));
    $phs  = implode(', ', array_fill(0, count($data), '?'));
    $newId = db_exec("INSERT INTO collection_schedules ($cols) VALUES ($phs)", array_values($data));
    json_out(['success'=>true, 'id'=>(int)$newId], 201);
}

// PUT (update)
if ($method === 'PUT') {
    if (!$id_raw) json_error('id required', 400);
    $sch = resolve_schedule($id_raw);
    if (!$sch) json_error('Schedule not found', 404);
    $body = body_json();
    $fields = ['name','schedule_type','enabled','priority','notes',
               'cron_minute','cron_hour','cron_day_of_month','cron_month','cron_day_of_week',
               'interval_value','interval_unit','next_run','last_run'];
    $sets = []; $params = [];
    foreach ($fields as $f) {
        if (array_key_exists($f, $body)) { $sets[] = "$f=?"; $params[] = $body[$f]; }
    }
    if (!$sets) json_error('No fields to update', 400);
    $sets[] = 'updated_at=NOW()';
    $params[] = $sch['id'];
    db_exec('UPDATE collection_schedules SET ' . implode(', ', $sets) . ' WHERE id=?', $params);
    json_out(['success'=>true]);
}

// DELETE
if ($method === 'DELETE') {
    if (!$id_raw) json_error('id required', 400);
    $sch = resolve_schedule($id_raw);
    if (!$sch) json_error('Schedule not found', 404);
    db_exec("DELETE FROM collection_schedules WHERE id=?", [$sch['id']]);
    json_out(['success'=>true]);
}

json_error('Method not allowed', 405);
