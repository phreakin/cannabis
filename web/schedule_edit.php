<?php
require_once __DIR__ . '/includes/functions.php';

$id  = get_int('id');
$sch = $id ? db_row("
    SELECT cs.*, ds.name AS source_name, ds.source_id AS src_id
    FROM   collection_schedules cs
    JOIN   data_sources ds ON ds.id=cs.source_id
    WHERE  cs.id=?", [$id]) : null;
$is_new = !$sch;

$page_title  = $is_new ? 'Add Schedule' : 'Edit Schedule: ' . ($sch['name'] ?? '');
$active_page = 'schedules';

// Handle POST
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_verify();

    $source_id_str = post_str('source_id');
    $ds = db_row("SELECT id FROM data_sources WHERE source_id=?", [$source_id_str]);
    if (!$ds) {
        $_SESSION['flash'][] = ['type'=>'danger','msg'=>'Invalid source selected.'];
    } else {
        $type = post_str('schedule_type', 'interval');
        $data = [
            'schedule_id'      => post_str('schedule_id'),
            'source_id'        => $ds['id'],
            'name'             => post_str('name'),
            'schedule_type'    => $type,
            'enabled'          => isset($_POST['enabled']) ? 1 : 0,
            'priority'         => post_int('priority', 2),
            'notes'            => post_str('notes'),
        ];
        if ($type === 'cron') {
            $data['cron_minute']       = post_str('cron_minute', '0');
            $data['cron_hour']         = post_str('cron_hour', '0');
            $data['cron_day_of_month'] = post_str('cron_day_of_month', '*');
            $data['cron_month']        = post_str('cron_month', '*');
            $data['cron_day_of_week']  = post_str('cron_day_of_week', '*');
            $data['interval_value']    = null;
            $data['interval_unit']     = null;
        } else {
            $data['interval_value']    = max(1, post_int('interval_value', 24));
            $data['interval_unit']     = post_str('interval_unit', 'hours');
            $data['cron_minute']       = '0';
            $data['cron_hour']         = '0';
            $data['cron_day_of_month'] = '*';
            $data['cron_month']        = '*';
            $data['cron_day_of_week']  = '*';
        }

        if (empty($data['schedule_id']) || empty($data['name'])) {
            $_SESSION['flash'][] = ['type'=>'danger','msg'=>'Schedule ID and Name are required.'];
        } elseif ($is_new) {
            $cols = implode(', ', array_keys($data));
            $phs  = implode(', ', array_fill(0, count($data), '?'));
            $newId = db_exec("INSERT INTO collection_schedules ($cols) VALUES ($phs)", array_values($data));
            $_SESSION['flash'][] = ['type'=>'success','msg'=>'Schedule created.'];
            redirect('schedule_edit.php?id=' . $newId);
        } else {
            $sets = implode(', ', array_map(fn($k) => "$k=?", array_keys($data)));
            db_exec("UPDATE collection_schedules SET $sets, updated_at=NOW() WHERE id=?",
                    array_merge(array_values($data), [$id]));
            $_SESSION['flash'][] = ['type'=>'success','msg'=>'Schedule updated.'];
            redirect('schedule_edit.php?id=' . $id);
        }
    }
}

$all_sources = get_all_sources();
require_once __DIR__ . '/includes/header.php';
$sch ??= [];   // treat null as empty array so $v() never warns on a new-form GET
$v = fn($k) => h($sch[$k] ?? '');
?>

<div class="d-flex align-items-center mb-3 gap-2">
  <a href="schedules.php" class="btn btn-sm btn-outline-secondary"><i class="bi bi-arrow-left me-1"></i>Back</a>
  <h5 class="mb-0"><?= $is_new ? 'Add New Schedule' : 'Edit Schedule' ?></h5>
</div>

<form method="post">
  <?= csrf_field() ?>
  <div class="row g-3">
    <div class="col-md-8">
      <div class="card mb-3">
        <div class="card-header border-secondary">Schedule Details</div>
        <div class="card-body row g-3">
          <div class="col-md-6">
            <label class="form-label">Schedule ID <span class="text-danger">*</span></label>
            <input type="text" name="schedule_id" class="form-control" required
                   value="<?= $v('schedule_id') ?>" <?= !$is_new?'readonly':'' ?>
                   placeholder="e.g. ca_dcc_daily">
          </div>
          <div class="col-md-6">
            <label class="form-label">Name <span class="text-danger">*</span></label>
            <input type="text" name="name" class="form-control" required value="<?= $v('name') ?>">
          </div>
          <div class="col-12">
            <label class="form-label">Source <span class="text-danger">*</span></label>
            <select name="source_id" class="form-select" required>
              <option value="">— Select Source —</option>
              <?php foreach ($all_sources as $s): ?>
              <option value="<?= h($s['source_id']) ?>"
                <?= (($sch['src_id'] ?? '') === $s['source_id']) ? 'selected' : '' ?>>
                [<?= h($s['state']) ?>] <?= h($s['name']) ?>
              </option>
              <?php endforeach; ?>
            </select>
          </div>

          <div class="col-md-4">
            <label class="form-label">Type</label>
            <select name="schedule_type" class="form-select" id="schedType" onchange="toggleType(this.value)">
              <option value="interval" <?= ($sch['schedule_type']??'interval')==='interval'?'selected':'' ?>>Interval</option>
              <option value="cron"     <?= ($sch['schedule_type']??'')==='cron'?'selected':'' ?>>Cron</option>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Priority</label>
            <select name="priority" class="form-select">
              <option value="1" <?= ($sch['priority']??2)==1?'selected':'' ?>>High</option>
              <option value="2" <?= ($sch['priority']??2)==2?'selected':'' ?>>Normal</option>
              <option value="3" <?= ($sch['priority']??2)==3?'selected':'' ?>>Low</option>
            </select>
          </div>

          <!-- Interval fields -->
          <div id="intervalFields" class="col-12 row g-2">
            <div class="col-md-4">
              <label class="form-label">Every</label>
              <input type="number" name="interval_value" class="form-control" min="1"
                     value="<?= h($sch['interval_value'] ?? 24) ?>">
            </div>
            <div class="col-md-4">
              <label class="form-label">Unit</label>
              <select name="interval_unit" class="form-select">
                <?php foreach (['minutes','hours','days','weeks'] as $u): ?>
                <option value="<?= $u ?>" <?= ($sch['interval_unit']??'hours')===$u?'selected':'' ?>><?= ucfirst($u) ?></option>
                <?php endforeach; ?>
              </select>
            </div>
          </div>

          <!-- Cron fields -->
          <div id="cronFields" class="col-12 row g-2" style="display:none">
            <div class="form-text mb-1 col-12">Cron expression (minute hour day-of-month month day-of-week)</div>
            <?php foreach (['cron_minute'=>'Minute','cron_hour'=>'Hour','cron_day_of_month'=>'Day (month)','cron_month'=>'Month','cron_day_of_week'=>'Day (week)'] as $cn => $cl): ?>
            <div class="col">
              <label class="form-label small"><?= $cl ?></label>
              <input type="text" name="<?= $cn ?>" class="form-control form-control-sm font-monospace"
                     value="<?= $v($cn) ?: '*' ?>">
            </div>
            <?php endforeach; ?>
          </div>

          <div class="col-12">
            <label class="form-label">Notes</label>
            <textarea name="notes" class="form-control" rows="2"><?= $v('notes') ?></textarea>
          </div>
        </div>
      </div>
    </div>

    <div class="col-md-4">
      <div class="card mb-3">
        <div class="card-header border-secondary">Status</div>
        <div class="card-body">
          <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" name="enabled" id="chkEnabled"
                   <?= ($sch['enabled'] ?? 1) ? 'checked' : '' ?>>
            <label class="form-check-label" for="chkEnabled">Enabled</label>
          </div>
        </div>
      </div>

      <?php if (!$is_new): ?>
      <div class="card mb-3">
        <div class="card-header border-secondary">Run History</div>
        <div class="card-body">
          <?php
          $runs = db_all("SELECT status, COUNT(*) AS cnt FROM collection_runs WHERE schedule_id=? GROUP BY status", [$id]);
          $lastRun = db_val("SELECT MAX(started_at) FROM collection_runs WHERE schedule_id=?", [$id]);
          ?>
          <?php foreach ($runs as $r): ?>
          <div class="d-flex justify-content-between mb-2">
            <?= status_badge($r['status']) ?>
            <strong><?= h($r['cnt']) ?></strong>
          </div>
          <?php endforeach; ?>
          <?php if ($lastRun): ?>
          <hr class="border-secondary my-2">
          <div class="text-secondary small">Last run: <?= h(fmt_date($lastRun)) ?></div>
          <?php endif; ?>
        </div>
      </div>
      <?php endif; ?>

      <div class="d-grid gap-2">
        <button type="submit" class="btn btn-success">
          <i class="bi bi-check-lg me-1"></i><?= $is_new ? 'Create Schedule' : 'Save Changes' ?>
        </button>
        <a href="schedules.php" class="btn btn-outline-secondary">Cancel</a>
      </div>
    </div>
  </div>
</form>

<?php
$initType = ($sch['schedule_type'] ?? 'interval');
$extra_js = <<<JS
<script>
function toggleType(t) {
  document.getElementById('intervalFields').style.display = t === 'interval' ? '' : 'none';
  document.getElementById('cronFields').style.display     = t === 'cron'     ? '' : 'none';
}
toggleType('$initType');
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
