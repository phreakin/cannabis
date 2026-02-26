<?php
/**
 * api/records.php – Read + export raw_records.
 *
 * GET  api/records.php                       – paginated list
 * GET  api/records.php?id=N                  – single record
 * GET  api/records.php?action=export&fmt=csv – CSV download
 * GET  api/records.php?action=geojson        – GeoJSON feature collection
 */
require_once dirname(__DIR__) . '/includes/functions.php';
require_method('GET');

$action   = get_str('action');
$id       = get_int('id');

// ── Build common WHERE from filter params ─────────────────────────────────────
function records_where(): array {
    $where = []; $params = [];
    $state    = get_str('state');
    $category = get_str('category');
    $status   = get_str('license_status');
    $gps      = get_str('gps');
    $q        = get_str('q');
    $src_str  = get_str('source');

    if ($state)    { $where[] = 'r.state = ?';          $params[] = $state; }
    if ($category) { $where[] = 'r.category = ?';       $params[] = $category; }
    if ($status)   { $where[] = 'r.license_status = ?'; $params[] = $status; }
    if ($gps === '1') $where[] = 'r.latitude IS NOT NULL AND r.longitude IS NOT NULL';
    if ($src_str) {
        $ds = db_row("SELECT id FROM data_sources WHERE source_id=?", [$src_str]);
        if ($ds) { $where[] = 'r.source_id = ?'; $params[] = $ds['id']; }
    }
    if ($q) {
        $where[] = '(r.name LIKE ? OR r.license_number LIKE ? OR r.city LIKE ?)';
        $qs = "%$q%"; $params = array_merge($params, [$qs,$qs,$qs]);
    }
    return [$where, $params];
}

// ── Single record ─────────────────────────────────────────────────────────────
if ($id) {
    $row = db_row("
        SELECT r.*, ds.name AS source_name, ds.source_id
        FROM   raw_records r
        JOIN   data_sources ds ON ds.id = r.source_id
        WHERE  r.id=?", [$id]);
    if (!$row) json_error('Record not found', 404);
    $row['record_data'] = $row['record_data'] ? json_decode($row['record_data'], true) : null;
    json_out(['record' => $row]);
}

// ── GeoJSON export ────────────────────────────────────────────────────────────
if ($action === 'geojson') {
    [$where, $params] = records_where();
    $where[] = 'r.latitude IS NOT NULL AND r.longitude IS NOT NULL';
    $wclause = 'WHERE ' . implode(' AND ', $where);
    $limit   = min(MAX_EXPORT_ROWS, max(1, get_int('limit', 50000)));
    $params[] = $limit;

    $rows = db_all("
        SELECT r.id, r.name, r.state, r.category, r.license_number, r.license_status,
               r.license_type, r.address, r.city, r.zip_code, r.county,
               r.latitude, r.longitude, r.phone, r.email, r.website, r.record_date,
               ds.name AS source_name, ds.source_id
        FROM   raw_records r
        JOIN   data_sources ds ON ds.id = r.source_id
        $wclause
        ORDER  BY r.id DESC LIMIT ?", $params);

    $features = [];
    foreach ($rows as $r) {
        $props = $r;
        unset($props['latitude'], $props['longitude']);
        $features[] = [
            'type'       => 'Feature',
            'geometry'   => ['type'=>'Point','coordinates'=>[(float)$r['longitude'],(float)$r['latitude']]],
            'properties' => $props,
        ];
    }
    header('Content-Type: application/geo+json; charset=utf-8');
    echo json_encode(['type'=>'FeatureCollection','features'=>$features], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

// ── CSV/JSON file export ──────────────────────────────────────────────────────
if ($action === 'export') {
    [$where, $params] = records_where();
    $wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';
    $limit   = min(MAX_EXPORT_ROWS, max(0, get_int('limit', 0)));
    $fmt     = get_str('fmt', 'csv');

    $sql = "
        SELECT r.id, r.state, r.category, r.subcategory, r.name, r.license_number,
               r.license_type, r.license_status, r.address, r.city, r.zip_code, r.county,
               r.latitude, r.longitude, r.phone, r.email, r.website,
               r.record_date, r.license_date, r.expiry_date, r.created_at,
               ds.name AS source_name, ds.source_id
        FROM   raw_records r
        JOIN   data_sources ds ON ds.id = r.source_id
        $wclause
        ORDER  BY r.created_at DESC";
    if ($limit > 0) { $sql .= ' LIMIT ?'; $params[] = $limit; }

    $ts = date('Ymd_His');

    if ($fmt === 'json') {
        $rows = db_all($sql, $params);
        header('Content-Type: application/json; charset=utf-8');
        header("Content-Disposition: attachment; filename=\"cannabis_records_{$ts}.json\"");
        echo json_encode(['exported_at'=>date('c'),'count'=>count($rows),'records'=>$rows],
                         JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        exit;
    }

    // CSV (stream row-by-row)
    header('Content-Type: text/csv; charset=utf-8');
    header("Content-Disposition: attachment; filename=\"cannabis_records_{$ts}.csv\"");
    $out = fopen('php://output', 'w');
    fwrite($out, "\xEF\xBB\xBF"); // UTF-8 BOM for Excel

    $header_written = false;
    $pdo = db();
    $st  = $pdo->prepare($sql);
    $st->execute($params);
    while ($row = $st->fetch()) {
        if (!$header_written) {
            fputcsv($out, array_keys($row));
            $header_written = true;
        }
        fputcsv($out, $row);
    }
    fclose($out);
    exit;
}

// ── Paginated list ────────────────────────────────────────────────────────────
[$where, $params] = records_where();
$wclause  = $where ? 'WHERE ' . implode(' AND ', $where) : '';
$page     = max(1, get_int('page', 1));
$per_page = min(200, max(1, get_int('per_page', 50)));
$total    = (int)db_val("SELECT COUNT(*) FROM raw_records r $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);

$rows = db_all("
    SELECT r.id, r.state, r.category, r.name, r.license_number, r.license_type,
           r.license_status, r.city, r.county, r.zip_code, r.address,
           r.latitude, r.longitude, r.phone, r.email, r.record_date, r.created_at,
           ds.name AS source_name, ds.source_id
    FROM   raw_records r
    JOIN   data_sources ds ON ds.id = r.source_id
    $wclause
    ORDER  BY r.created_at DESC LIMIT ? OFFSET ?",
    array_merge($params, [$limit, $offset]));

json_out(array_merge(paginate($total, $page, $per_page), ['records' => $rows]));
