<?php
$page_title  = 'Schedules';
$active_page = 'schedules';
require_once __DIR__ . '/includes/header.php';

$f_source  = get_str('source');
$f_enabled = get_str('enabled', 'all');
$page      = max(1, get_int('page', 1));
$per_page  = 50;

$where = []; $params = [];
if ($f_source)             { $where[] = 'ds.source_id = ?'; $params[] = $f_source; }
if ($f_enabled === '1')    { $where[] = 'cs.enabled = 1'; }
if ($f_enabled === '0')    { $where[] = 'cs.enabled = 0'; }
$wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

$total = (int)db_val("SELECT COUNT(*) FROM collection_schedules cs JOIN data_sources ds ON ds.id=cs.source_id $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);
$pg = paginate($total, $page, $per_page);

$schedules = db_all("
    SELECT cs.*, ds.name AS source_name, ds.source_id AS src_id, ds.state, ds.category,
           (SELECT COUNT(*) FROM collection_runs cr WHERE cr.schedule_id=cs.id) AS run_count,
           (SELECT MAX(cr.started_at) FROM collection_runs cr WHERE cr.schedule_id=cs.id) AS last_run_at,
           (SELECT cr.status FROM collection_runs cr WHERE cr.schedule_id=cs.id ORDER BY cr.started_at DESC LIMIT 1) AS last_status
    FROM   collection_schedules cs
    JOIN   data_sources ds ON ds.id = cs.source_id
    $wclause
    ORDER  BY cs.enabled DESC, ds.state, ds.name
    LIMIT  ? OFFSET ?
", array_merge($params, [$limit, $offset]));

$all_sources = get_all_sources();
?>

<!-- Filter bar -->
<form method="get" class="filter-bar p-3 mb-4">
  <div class="row g-2 align-items-end">
    <div class="col-md-4">
      <label class="form-label small mb-1">Source</label>
      <select name="source" class="form-select form-select-sm">
        <option value="">All Sources</option>
        <?php foreach ($all_sources as $s): ?>
        <option value="<?= h($s['source_id']) ?>" <?= $f_source===$s['source_id']?'selected':'' ?>>
          <?= h($s['name']) ?> (<?= h($s['state']) ?>)
        </option>
        <?php endforeach; ?>
      </select>
    </div>
    <div class="col-md-2">
      <label class="form-label small mb-1">Status</label>
      <select name="enabled" class="form-select form-select-sm">
        <option value="all" <?= $f_enabled==='all'?'selected':'' ?>>All</option>
        <option value="1"   <?= $f_enabled==='1'?'selected':'' ?>>Enabled</option>
        <option value="0"   <?= $f_enabled==='0'?'selected':'' ?>>Disabled</option>
      </select>
    </div>
    <div class="col-auto">
      <button type="submit" class="btn btn-sm btn-success">Filter</button>
    </div>
  </div>
</form>

<!-- Toolbar -->
<div class="d-flex align-items-center mb-3 gap-2">
  <span class="text-secondary small"><?= h(number_format($total)) ?> schedule<?= $total!==1?'s':'' ?></span>
  <a href="schedule_edit.php" class="btn btn-sm btn-success ms-auto">
    <i class="bi bi-plus-lg me-1"></i>Add Schedule
  </a>
</div>

<!-- Table -->
<?php if (empty($schedules)): ?>
<div class="empty-state"><i class="bi bi-clock"></i>No schedules found.</div>
<?php else: ?>
<div class="card">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-hover table-sm mb-0">
        <thead class="table-dark">
          <tr>
            <th>Schedule</th><th>Source</th><th>Type</th><th>Expression</th>
            <th>Priority</th><th>Last Run</th><th>Next Run</th><th>Last Status</th>
            <th>Runs</th><th>Status</th><th class="text-end">Actions</th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($schedules as $sch): ?>
          <?php
          // Build human expression
          if ($sch['schedule_type'] === 'interval') {
              $expr = $sch['interval_value'] . ' ' . $sch['interval_unit'];
          } else {
              $expr = implode(' ', [
                  $sch['cron_minute'], $sch['cron_hour'],
                  $sch['cron_day_of_month'], $sch['cron_month'], $sch['cron_day_of_week']
              ]);
          }
          $priorityLabel = ['1'=>'High','2'=>'Normal','3'=>'Low'][$sch['priority']] ?? $sch['priority'];
          ?>
          <tr>
            <td>
              <a href="schedule_edit.php?id=<?= h($sch['id']) ?>" class="fw-semibold text-decoration-none">
                <?= h($sch['name']) ?>
              </a>
            </td>
            <td>
              <a href="source_edit.php?id=<?= h($sch['source_id']) ?>" class="text-decoration-none">
                <?= h($sch['source_name']) ?>
              </a>
              <span class="badge bg-secondary ms-1"><?= h($sch['state']) ?></span>
            </td>
            <td><span class="badge bg-info text-dark"><?= h($sch['schedule_type']) ?></span></td>
            <td><code class="text-success"><?= h($expr) ?></code></td>
            <td><?= h($priorityLabel) ?></td>
            <td class="text-secondary small" title="<?= h($sch['last_run_at']) ?>">
              <?= $sch['last_run_at'] ? h(time_ago($sch['last_run_at'])) : '–' ?>
            </td>
            <td class="small" title="<?= h($sch['next_run']) ?>">
              <?= $sch['next_run'] ? h(fmt_date($sch['next_run'])) : '–' ?>
            </td>
            <td><?= $sch['last_status'] ? status_badge($sch['last_status']) : '–' ?></td>
            <td><?= h(number_format($sch['run_count'])) ?></td>
            <td>
              <?= $sch['enabled']
                ? '<span class="badge bg-success">Enabled</span>'
                : '<span class="badge bg-secondary">Disabled</span>' ?>
            </td>
            <td class="text-end">
              <div class="btn-group btn-group-sm">
                <a href="schedule_edit.php?id=<?= h($sch['id']) ?>" class="btn btn-outline-secondary" title="Edit">
                  <i class="bi bi-pencil"></i>
                </a>
                <?php if ($sch['enabled']): ?>
                <button class="btn btn-outline-warning" title="Disable"
                        onclick="toggleSchedule('<?= h($sch['schedule_id']) ?>',false)">
                  <i class="bi bi-pause-fill"></i>
                </button>
                <?php else: ?>
                <button class="btn btn-outline-success" title="Enable"
                        onclick="toggleSchedule('<?= h($sch['schedule_id']) ?>',true)">
                  <i class="bi bi-play"></i>
                </button>
                <?php endif; ?>
                <button class="btn btn-outline-danger" title="Delete"
                        onclick="deleteSchedule('<?= h($sch['schedule_id']) ?>','<?= h(addslashes($sch['name'])) ?>')">
                  <i class="bi bi-trash"></i>
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
    <?php for ($i=1;$i<=$pg['pages'];$i++): $q=http_build_query(array_merge($_GET,['page'=>$i])); ?>
    <li class="page-item <?= $i===$page?'active':'' ?>"><a class="page-link" href="?<?= h($q) ?>"><?= $i ?></a></li>
    <?php endfor; ?>
  </ul>
</nav>
<?php endif; ?>
<?php endif; ?>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
