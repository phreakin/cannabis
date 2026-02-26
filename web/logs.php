<?php
$page_title  = 'Collection Logs';
$active_page = 'logs';
require_once __DIR__ . '/includes/header.php';

$f_level  = get_str('level');
$f_source = get_str('source');
$f_since  = get_str('since');   // e.g. 2024-01-01
$f_search = get_str('q');
$page     = max(1, get_int('page', 1));
$per_page = 100;

$where = []; $params = [];
if ($f_level)  { $where[] = 'cl.level = ?';   $params[] = strtoupper($f_level); }
if ($f_search) { $where[] = 'cl.message LIKE ?'; $params[] = "%$f_search%"; }
if ($f_since)  { $where[] = 'cl.timestamp >= ?'; $params[] = $f_since . ' 00:00:00'; }
if ($f_source) {
    $dsRow = db_row("SELECT id FROM data_sources WHERE source_id=?", [$f_source]);
    if ($dsRow) { $where[] = 'cl.source_id = ?'; $params[] = $dsRow['id']; }
}
$wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

$total = (int)db_val("SELECT COUNT(*) FROM collection_logs cl $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);
$pg = paginate($total, $page, $per_page);

$logs = db_all("
    SELECT cl.id, cl.level, cl.message, cl.details, cl.timestamp,
           cl.run_id, cl.source_id,
           ds.name AS source_name
    FROM   collection_logs cl
    LEFT   JOIN data_sources ds ON ds.id = cl.source_id
    $wclause
    ORDER  BY cl.timestamp DESC
    LIMIT  ? OFFSET ?
", array_merge($params, [$limit, $offset]));

$sources = get_all_sources();
?>

<!-- Filter bar -->
<form method="get" class="filter-bar p-3 mb-4">
  <div class="row g-2 align-items-end">
    <div class="col-md-3">
      <label class="form-label small mb-1">Search message</label>
      <input type="text" name="q" class="form-control form-control-sm"
             placeholder="Search…" value="<?= h($f_search) ?>">
    </div>
    <div class="col-md-2">
      <label class="form-label small mb-1">Level</label>
      <select name="level" class="form-select form-select-sm">
        <option value="">All Levels</option>
        <?php foreach (['DEBUG','INFO','WARNING','ERROR'] as $lv): ?>
        <option value="<?= $lv ?>" <?= strtoupper($f_level)===$lv?'selected':'' ?>><?= $lv ?></option>
        <?php endforeach; ?>
      </select>
    </div>
    <div class="col-md-3">
      <label class="form-label small mb-1">Source</label>
      <select name="source" class="form-select form-select-sm">
        <option value="">All Sources</option>
        <?php foreach ($sources as $s): ?>
        <option value="<?= h($s['source_id']) ?>" <?= $f_source===$s['source_id']?'selected':'' ?>>
          <?= h($s['name']) ?>
        </option>
        <?php endforeach; ?>
      </select>
    </div>
    <div class="col-md-2">
      <label class="form-label small mb-1">Since Date</label>
      <input type="date" name="since" class="form-control form-control-sm" value="<?= h($f_since) ?>">
    </div>
    <div class="col-md-1">
      <button type="submit" class="btn btn-sm btn-success w-100">Filter</button>
    </div>
    <?php if ($f_level||$f_source||$f_since||$f_search): ?>
    <div class="col-md-1">
      <a href="logs.php" class="btn btn-sm btn-outline-secondary w-100">Clear</a>
    </div>
    <?php endif; ?>
  </div>
</form>

<!-- Toolbar -->
<div class="d-flex align-items-center mb-3 gap-2">
  <span class="text-secondary small"><?= h(number_format($total)) ?> log entr<?= $total!==1?'ies':'y' ?></span>
  <button class="btn btn-sm btn-outline-danger ms-auto" onclick="purgeLogs()">
    <i class="bi bi-trash me-1"></i>Purge Old Logs
  </button>
</div>

<!-- Log table -->
<?php if (empty($logs)): ?>
<div class="empty-state"><i class="bi bi-journal-x"></i>No log entries found.</div>
<?php else: ?>
<div class="card">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-sm mb-0 table-hover" id="logTable">
        <thead class="table-dark">
          <tr>
            <th style="width:160px">Timestamp</th>
            <th style="width:90px">Level</th>
            <th style="width:180px">Source</th>
            <th>Message</th>
            <th style="width:70px">Run</th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($logs as $log):
            $lvClass = 'log-' . strtolower($log['level']); ?>
          <tr class="<?= h($lvClass) ?> cursor-pointer" onclick="showLogDetail(this)"
              data-details="<?= h(json_encode($log['details'] ?? [])) ?>"
              data-msg="<?= h($log['message']) ?>">
            <td class="font-monospace small"><?= h(fmt_date($log['timestamp'], 'Y-m-d H:i:s')) ?></td>
            <td><?= level_badge($log['level']) ?></td>
            <td class="small"><?= h($log['source_name'] ?? '–') ?></td>
            <td class="small text-truncate-2"><?= h($log['message']) ?></td>
            <td class="small text-secondary"><?= $log['run_id'] ? '#'.h($log['run_id']) : '–' ?></td>
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
    <?php
    $start = max(1, $page - 4); $end = min($pg['pages'], $page + 4);
    for ($i=$start;$i<=$end;$i++): $q=http_build_query(array_merge($_GET,['page'=>$i])); ?>
    <li class="page-item <?= $i===$page?'active':'' ?>"><a class="page-link" href="?<?= h($q) ?>"><?= $i ?></a></li>
    <?php endfor; ?>
  </ul>
</nav>
<?php endif; ?>
<?php endif; ?>

<!-- Log detail modal -->
<div class="modal fade" id="logDetailModal" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header border-secondary">
        <h5 class="modal-title">Log Entry</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <p id="logDetailMsg" class="mb-3"></p>
        <pre id="logDetailJson" class="json-pre p-3" style="display:none"></pre>
      </div>
    </div>
  </div>
</div>

<?php
$extra_js = <<<'JS'
<script>
function showLogDetail(row) {
  document.getElementById('logDetailMsg').textContent = row.dataset.msg;
  const det = JSON.parse(row.dataset.details || '{}');
  const pre = document.getElementById('logDetailJson');
  if (det && Object.keys(det).length) {
    pre.textContent = JSON.stringify(det, null, 2);
    pre.style.display = '';
  } else {
    pre.style.display = 'none';
  }
  bootstrap.Modal.getOrCreateInstance(document.getElementById('logDetailModal')).show();
}

function purgeLogs() {
  const days = prompt('Purge logs older than how many days?', '90');
  if (!days || isNaN(days)) return;
  apiPost(_api('api/logs.php?action=purge'), { days: parseInt(days) })
    .then(r => { showToast(r.message ?? 'Logs purged'); setTimeout(() => location.reload(), 1000); })
    .catch(e => showToast(e.message, 'danger'));
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
