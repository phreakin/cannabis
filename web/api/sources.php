<?php
/**
 * api/sources.php – CRUD + actions for data_sources.
 *
 * GET    api/sources.php             – list sources (paginated)
 * GET    api/sources.php?id=N        – single source
 * POST   api/sources.php             – create source (JSON body)
 * PUT    api/sources.php?id=N        – update source (JSON body)
 * DELETE api/sources.php?id=N        – delete source
 * POST   api/sources.php?action=enable&id=SRC_ID   – enable
 * POST   api/sources.php?action=disable&id=SRC_ID  – disable
 * POST   api/sources.php?action=run&id=SRC_ID      – trigger run (queues a background job)
 */
require_once dirname(__DIR__) . '/includes/functions.php';

$method = $_SERVER['REQUEST_METHOD'];
$action = get_str('action');
$id_raw = get_str('id');   // may be numeric row id or source_id string

// ── Helper: resolve either int id or source_id string → row ──────────────────
function resolve_source(string $id_raw): ?array {
    if (ctype_digit($id_raw)) {
        return db_row("SELECT * FROM data_sources WHERE id=?", [(int)$id_raw]);
    }
    return db_row("SELECT * FROM data_sources WHERE source_id=?", [$id_raw]);
}

// ── Actions (POST with ?action=…) ─────────────────────────────────────────────
if ($action) {
    require_method('POST');
    $src = resolve_source($id_raw);
    if (!$src) json_error('Source not found', 404);

    if ($action === 'enable') {
        db_exec("UPDATE data_sources SET enabled=1, updated_at=NOW() WHERE id=?", [$src['id']]);
        json_out(['success'=>true, 'message'=>'Source enabled']);
    }
    if ($action === 'disable') {
        db_exec("UPDATE data_sources SET enabled=0, updated_at=NOW() WHERE id=?", [$src['id']]);
        json_out(['success'=>true, 'message'=>'Source disabled']);
    }
    if ($action === 'run') {
        // Write a trigger file that the Python scheduler watches, or just log intent
        $triggerDir = APP_ROOT . '/data/triggers';
        if (!is_dir($triggerDir)) @mkdir($triggerDir, 0755, true);
        file_put_contents("$triggerDir/{$src['source_id']}.trigger", json_encode([
            'source_id'    => $src['source_id'],
            'triggered_at' => date('c'),
            'triggered_by' => 'web_api',
        ]));
        json_out(['success'=>true, 'message'=>"Collection queued for {$src['name']}"]);
    }
    json_error('Unknown action', 400);
}

// ── GET single ────────────────────────────────────────────────────────────────
if ($method === 'GET' && $id_raw !== '') {
    $src = resolve_source($id_raw);
    if (!$src) json_error('Source not found', 404);
    // Decode JSON fields
    foreach (['params','headers','field_mapping','tags','pagination'] as $jf) {
        $src[$jf] = $src[$jf] ? json_decode($src[$jf], true) : null;
    }
    // Augment with stats
    $src['record_count']   = (int)db_val("SELECT COUNT(*) FROM raw_records WHERE source_id=?", [$src['id']]);
    $src['schedule_count'] = (int)db_val("SELECT COUNT(*) FROM collection_schedules WHERE source_id=?", [$src['id']]);
    $src['last_run']       = db_val("SELECT MAX(started_at) FROM collection_runs WHERE source_id=?", [$src['id']]);
    json_out(['source' => $src]);
}

// ── GET list ──────────────────────────────────────────────────────────────────
if ($method === 'GET') {
    $page     = max(1, get_int('page', 1));
    $per_page = min(200, max(1, get_int('per_page', 50)));
    $state    = get_str('state');
    $category = get_str('category');
    $enabled  = get_str('enabled');
    $q        = get_str('q');

    $where = []; $params = [];
    if ($state)   { $where[] = 'state = ?';    $params[] = $state; }
    if ($category){ $where[] = 'category = ?'; $params[] = $category; }
    if ($enabled === '1') $where[] = 'enabled = 1';
    if ($enabled === '0') $where[] = 'enabled = 0';
    if ($q)       { $where[] = '(name LIKE ? OR source_id LIKE ?)';
                    $qs = "%$q%"; $params = array_merge($params, [$qs, $qs]); }
    $wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    $total = (int)db_val("SELECT COUNT(*) FROM data_sources $wclause", $params);
    [$limit, $offset] = limit_offset($page, $per_page);

    $rows = db_all("SELECT id, source_id, name, state, category, format, enabled,
                           url, agency, description, tags, created_at, updated_at
                    FROM data_sources $wclause ORDER BY state, name LIMIT ? OFFSET ?",
                   array_merge($params, [$limit, $offset]));
    foreach ($rows as &$r) {
        $r['tags'] = $r['tags'] ? json_decode($r['tags'], true) : [];
    }
    json_out(array_merge(paginate($total, $page, $per_page), ['sources' => $rows]));
}

// ── POST (create) ─────────────────────────────────────────────────────────────
if ($method === 'POST') {
    $body = body_json();
    $required = ['source_id','name','state','category','format'];
    foreach ($required as $r) {
        if (empty($body[$r])) json_error("Field '$r' is required");
    }
    $json_fields = ['params','headers','field_mapping','tags','pagination'];
    $data = [
        'source_id'        => $body['source_id'],
        'name'             => $body['name'],
        'description'      => $body['description'] ?? null,
        'state'            => $body['state'],
        'agency'           => $body['agency'] ?? null,
        'category'         => $body['category'],
        'subcategory'      => $body['subcategory'] ?? null,
        'format'           => $body['format'],
        'url'              => $body['url'] ?? null,
        'discovery_url'    => $body['discovery_url'] ?? null,
        'website'          => $body['website'] ?? null,
        'enabled'          => isset($body['enabled']) ? (int)$body['enabled'] : 1,
        'api_key_required' => isset($body['api_key_required']) ? (int)$body['api_key_required'] : 0,
        'api_key_env'      => $body['api_key_env'] ?? null,
        'notes'            => $body['notes'] ?? null,
        'rate_limit_rpm'   => (int)($body['rate_limit_rpm'] ?? 60),
        'timeout'          => (int)($body['timeout'] ?? 60),
    ];
    foreach ($json_fields as $jf) {
        $data[$jf] = isset($body[$jf]) ? json_encode($body[$jf]) : null;
    }
    $cols = implode(', ', array_keys($data));
    $phs  = implode(', ', array_fill(0, count($data), '?'));
    $newId = db_exec("INSERT INTO data_sources ($cols) VALUES ($phs)", array_values($data));
    json_out(['success'=>true, 'id'=>(int)$newId], 201);
}

// ── PUT (update) ──────────────────────────────────────────────────────────────
if ($method === 'PUT') {
    if (!$id_raw) json_error('id required', 400);
    $src = resolve_source($id_raw);
    if (!$src) json_error('Source not found', 404);

    $body   = body_json();
    $fields = ['name','description','state','agency','category','subcategory','format',
               'url','discovery_url','website','enabled','api_key_required','api_key_env',
               'notes','rate_limit_rpm','timeout'];
    $json_fields = ['params','headers','field_mapping','tags','pagination'];
    $sets = []; $params = [];
    foreach ($fields as $f) {
        if (array_key_exists($f, $body)) { $sets[] = "$f=?"; $params[] = $body[$f]; }
    }
    foreach ($json_fields as $jf) {
        if (array_key_exists($jf, $body)) { $sets[] = "$jf=?"; $params[] = json_encode($body[$jf]); }
    }
    if (!$sets) json_error('No fields to update', 400);
    $sets[] = 'updated_at=NOW()';
    $params[] = $src['id'];
    db_exec('UPDATE data_sources SET ' . implode(', ', $sets) . ' WHERE id=?', $params);
    json_out(['success'=>true]);
}

// ── DELETE ────────────────────────────────────────────────────────────────────
if ($method === 'DELETE') {
    if (!$id_raw) json_error('id required', 400);
    $src = resolve_source($id_raw);
    if (!$src) json_error('Source not found', 404);
    db_exec("DELETE FROM data_sources WHERE id=?", [$src['id']]);
    json_out(['success'=>true]);
}

json_error('Method not allowed', 405);
