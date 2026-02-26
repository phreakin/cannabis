<?php
$page_title = 'Data Sources';
$active_page = 'sources';
require_once __DIR__ . '/includes/header.php';

// Filters
$f_state = get_str('state');
$f_category = get_str('category');
$f_format = get_str('format');
$f_enabled = get_str('enabled', 'all');
$f_search = get_str('q');
$page = max(1, get_int('page', 1));
$per_page = 50;

// Build WHERE
$where = [];
$params = [];
if ($f_state) {
    $where[] = 'ds.state = ?';
    $params[] = $f_state;
}
if ($f_category) {
    $where[] = 'ds.category = ?';
    $params[] = $f_category;
}
if ($f_format) {
    $where[] = 'ds.format = ?';
    $params[] = $f_format;
}
if ($f_enabled === '1') {
    $where[] = 'ds.enabled = 1';
}
if ($f_enabled === '0') {
    $where[] = 'ds.enabled = 0';
}
if ($f_search) {
    $where[] = '(ds.name LIKE ? OR ds.source_id LIKE ? OR ds.agency LIKE ?)';
    $s = "%$f_search%";
    $params = array_merge($params, [$s, $s, $s]);
}
$wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

$total = (int)db_val("SELECT COUNT(*) FROM data_sources ds $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);
$pg = paginate($total, $page, $per_page);

$sources = db_all("
    SELECT ds.*,
           COUNT(DISTINCT cs.id) AS schedule_count,
           COUNT(DISTINCT cr.id) AS run_count,
           COUNT(DISTINCT rr.id) AS record_count,
           MAX(cr.started_at)    AS last_run
    FROM   data_sources ds
    LEFT   JOIN collection_schedules cs ON cs.source_id = ds.id
    LEFT   JOIN collection_runs      cr ON cr.source_id = ds.id
    LEFT   JOIN raw_records          rr ON rr.source_id = ds.id
    $wclause
    GROUP  BY ds.id
    ORDER  BY ds.state, ds.name
    LIMIT  ? OFFSET ?
", array_merge($params, [$limit, $offset]));

$states = db_all("SELECT DISTINCT state FROM data_sources ORDER BY state");
$categories = db_all("SELECT DISTINCT category FROM data_sources ORDER BY category");
$formats = db_all("SELECT DISTINCT format FROM data_sources ORDER BY format");
?>

<!-- Filter bar -->
<form method="get" class="filter-bar p-3 mb-4">
    <div class="row g-2 align-items-end">
        <div class="col-md-3">
            <label class="form-label small mb-1">
                <i class="fas fa-search me-2 text-success"></i>
                Search
            </label>
            <input type="text" name="q" class="form-control form-control-sm" placeholder="Name, ID, agency…" value="<?= h($f_search) ?>">
        </div>
        <div class="col-md-2">
            <label class="form-label small mb-1" for="state">
                <i class="fas fa-map-marker-alt me-2 text-success"></i>
                State
            </label>
            <select id="state" name="state" class="form-select form-select-sm">
                <option value="" <?= $f_state === '' ? 'selected' : '' ?>>
                    All States
                </option>
                <?php foreach ($states as $s): ?>
                    <option value="<?= h($s['state']) ?>" <?= $f_state === $s['state'] ? 'selected' : '' ?>><?= h($s['state']) ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-2">
            <label class="form-label small mb-1" for="category">
                <i class="fas fa-tag me-2 text-success"></i>
                Category
            </label>
            <select id="category" name="category" class="form-select form-select-sm">
                <option value="">All Categories</option>
                <?php foreach ($categories as $c): ?>
                    <option value="<?= h($c['category']) ?>" <?= $f_category === $c['category'] ? 'selected' : '' ?>><?= h($c['category']) ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-2">
            <label class="form-label small mb-1" for="format">
                <i class="fas fa-file-alt me-2 text-success"></i>
                Format
            </label>
            <select id="format" name="format" class="form-select form-select-sm">
                <option value="">All Formats</option>
                <?php foreach ($formats as $f): ?>
                    <option value="<?= h($f['format']) ?>" <?= $f_format === $f['format'] ? 'selected' : '' ?>><?= h(strtoupper($f['format'])) ?></option>
                <?php endforeach; ?>
            </select>
        </div>
        <div class="col-md-2">
            <label class="form-label small mb-1" for="enabled">
                <i class="fas fa-play me-2 text-success"></i>
                Status
            </label>
            <select id="enabled" name="enabled" class="form-select form-select-sm">
                <option value="all" <?= $f_enabled === 'all' ? 'selected' : '' ?>>All</option>
                <option value="1" <?= $f_enabled === '1' ? 'selected' : '' ?>>Enabled</option>
                <option value="0" <?= $f_enabled === '0' ? 'selected' : '' ?>>Disabled</option>
            </select>
        </div>
        <div class="col-md-1 d-flex gap-1">
            <button type="submit" class="btn btn-sm btn-success">
                <i class="fas fa-filter me-2"></i>
                Filter
            </button>
        </div>
    </div>
</form>

<!-- Toolbar -->
<div class="d-flex align-items-center mb-3 gap-2">
  <span class="text-secondary small">
      <?= h(number_format($total)) ?> source<?= $total !== 1 ? 's' : '' ?>
  </span>
    <a href="source_edit.php" class="btn btn-sm btn-success ms-auto">
        <i class="fas fa-plus me-1"></i>
        Add Source
    </a>
    <?php if ($f_state || $f_category || $f_format || $f_search || $f_enabled !== 'all'): ?>
        <a href="sources.php" class="btn btn-sm btn-outline-secondary">
            <i class="fas fa-times me-1"></i>
            Clear Filters
        </a>
    <?php endif; ?>
</div>

<!-- Table -->
<?php if (empty($sources)): ?>
    <div class="empty-state">
        <i class="fas fa-database fa-4x"></i>
        No sources match your filters.
    </div>
<?php else: ?>
    <div class="card">
        <div class="card-body p-0">
            <div class="table-responsive">
                <table class="table table-hover table-sm mb-0">
                    <thead class="table-dark">
                    <tr>
                        <th style="min-width:250px">
                            <i class="fas fa-database me-1"></i>
                            Name
                        </th>
                        <th style="width:100px">
                            <i class="fas fa-map-marker-alt me-1"></i>
                            State
                        </th>
                        <th style="width:150px">
                            <i class="fas fa-tag me-1"></i>
                            Category
                        </th>
                        <th style="width:120px">
                            <i class="fas fa-file-alt me-1"></i>
                            Format
                        </th>
                        <th style="width:120px">
                            <i class="fas fa-database me-1"></i>
                            Records
                        </th>
                        <th style="width:120px">
                            <i class="fas fa-calendar-alt me-1"></i>
                            Schedules
                        </th>
                        <th style="width:150px">
                            <i class="fas fa-history me-1"></i>
                            Last Run
                        </th>
                        <th style="width:120px">
                            <i class="fas fa-play me-1"></i>
                            Status
                        </th>
                        <th class="text-end">
                            <i class="fas fa-cogs me-1"></i>
                            Actions
                        </th>
                    </tr>
                    </thead>
                    <tbody>
                    <?php foreach ($sources as $src): ?>
                        <tr>
                            <td>
                                <a href="source_edit.php?id=<?= h($src['id']) ?>"
                                   class="fw-semibold text-decoration-none">
                                    <?= h($src['name']) ?>
                                </a>
                                <div class="text-secondary" style="font-size:.75rem">
                                    <?= h($src['source_id']) ?>
                                </div>
                            </td>
                            <td>
                <span class="badge bg-secondary">
                    <?= h($src['state']) ?>
                </span>
                            </td>
                            <td>
                                <?= h($src['category']) ?>
                            </td>
                            <td>
                                <?= format_badge($src['format']) ?>
                            </td>
                            <td>
                                <?= h(number_format($src['record_count'])) ?>
                            </td>
                            <td>
                                <?= h($src['schedule_count']) ?>
                            </td>
                            <td class="text-secondary small" title="<?= h($src['last_run']) ?>">
                                <?= $src['last_run'] ? h(time_ago($src['last_run'])) : '–' ?>
                            </td>
                            <td>
                                <?php if ($src['enabled']): ?>
                                    <span class="badge bg-success">
                                        <i class="fas fa-check me-1"></i>
                                        Enabled
                                    </span>
                                <?php else: ?>
                                    <span class="badge bg-secondary">
                                        <i class="fas fa-times me-1"></i>
                                        Disabled
                                    </span>
                                <?php endif; ?>
                            </td>
                            <td class="text-end">
                                <div class="btn-group btn-group-sm me-2">
                                    <button class="btn btn-outline-success me-2" title="Run now" onclick="runSource('<?= h($src['source_id']) ?>','<?= h(addslashes($src['name'])) ?>')">
                                        <i class="fas fa-play"></i>
                                    </button>
                                    <a href="source_edit.php?id=<?= h($src['id']) ?>" class="btn btn-outline-warning me-2" title="Edit">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    <?php if ($src['enabled']): ?>
                                        <button class="btn btn-outline-warning me-2" title="Disable" onclick="toggleSource('<?= h($src['source_id']) ?>',false)">
                                            <i class="fas fa-pause"></i>
                                        </button>
                                    <?php else: ?>
                                        <button class="btn btn-outline-success me-2" title="Enable"
                                                onclick="toggleSource('<?= h($src['source_id']) ?>',true)">
                                            <i class="fas fa-play"></i>
                                        </button>
                                    <?php endif; ?>
                                    <button class="btn btn-outline-danger me-2" title="Delete"
                                            onclick="deleteSource('<?= h($src['source_id']) ?>','<?= h(addslashes($src['name'])) ?>')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Pagination -->
    <?php if ($pg['pages'] > 1): ?>
        <nav class="mt-3">
            <ul class="pagination pagination-sm justify-content-center">
                <?php for ($i = 1; $i <= $pg['pages']; $i++):$q = http_build_query(array_merge($_GET, ['page' => $i])); ?>
                    <li class="page-item <?= $i === $page ? 'active' : '' ?>">
                        <a class="page-link" href="?<?= h($q) ?>">
                            <?= $i ?>
                        </a>
                    </li>
                <?php endfor; ?>
            </ul>
        </nav>
    <?php endif; ?>
<?php endif; ?>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
