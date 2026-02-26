<?php
$page_title  = 'Settings';
$active_page = 'settings';
require_once __DIR__ . '/includes/header.php';

// Handle POST
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_verify();

    $keys = [
        'collection_timeout', 'collection_rate_limit_rpm', 'collection_max_retries',
        'collection_retry_delay', 'storage_dedup_enabled', 'storage_max_records',
        'log_retention_days', 'log_level', 'dashboard_records_per_page', 'scheduler_enabled',
    ];
    foreach ($keys as $k) {
        if (isset($_POST[$k])) {
            set_setting($k, $_POST[$k]);
        }
    }
    // Checkboxes
    set_setting('storage_dedup_enabled', isset($_POST['storage_dedup_enabled']) ? 'true' : 'false');
    set_setting('scheduler_enabled', isset($_POST['scheduler_enabled']) ? 'true' : 'false');

    $_SESSION['flash'][] = ['type'=>'success','msg'=>'Settings saved.'];
    redirect('settings.php');
}

// Load all settings
$settings = [];
$rows = db_all("SELECT `key`, value, value_type, description, category FROM app_settings ORDER BY category, `key`");
foreach ($rows as $r) {
    $settings[$r['key']] = $r;
}

$sv = fn(string $k, mixed $default = '') => h($settings[$k]['value'] ?? $default);
$sb = fn(string $k) => ($settings[$k]['value'] ?? 'false') === 'true';

// DB stats
$tables = ['data_sources','collection_schedules','collection_runs','raw_records','collection_logs','app_settings'];
$counts = [];
foreach ($tables as $t) {
    $counts[$t] = (int)db_val("SELECT COUNT(*) FROM $t");
}
?>

<form method="post">
  <?= csrf_field() ?>
  <div class="row g-3">

    <!-- Left: settings form -->
    <div class="col-md-8">

      <!-- Collection settings -->
      <div class="card mb-3">
        <div class="card-header border-secondary">Collection Settings</div>
        <div class="card-body row g-3">
          <div class="col-md-4">
            <label class="form-label">Request Timeout (s)</label>
            <input type="number" name="collection_timeout" class="form-control" min="5" max="600"
                   value="<?= $sv('collection_timeout', 60) ?>">
          </div>
          <div class="col-md-4">
            <label class="form-label">Rate Limit (req/min)</label>
            <input type="number" name="collection_rate_limit_rpm" class="form-control" min="1" max="3600"
                   value="<?= $sv('collection_rate_limit_rpm', 60) ?>">
          </div>
          <div class="col-md-4">
            <label class="form-label">Max Retries</label>
            <input type="number" name="collection_max_retries" class="form-control" min="0" max="10"
                   value="<?= $sv('collection_max_retries', 3) ?>">
          </div>
          <div class="col-md-4">
            <label class="form-label">Retry Delay (s)</label>
            <input type="number" name="collection_retry_delay" class="form-control" min="1" max="300"
                   value="<?= $sv('collection_retry_delay', 5) ?>">
          </div>
          <div class="col-md-8 d-flex align-items-center">
            <div class="form-check form-switch">
              <input class="form-check-input" type="checkbox" name="scheduler_enabled" id="chkSched"
                     <?= $sb('scheduler_enabled') ? 'checked' : '' ?>>
              <label class="form-check-label" for="chkSched">Scheduler Enabled</label>
            </div>
          </div>
        </div>
      </div>

      <!-- Storage settings -->
      <div class="card mb-3">
        <div class="card-header border-secondary">Storage Settings</div>
        <div class="card-body row g-3">
          <div class="col-md-6">
            <label class="form-label">Max Records per Source (0 = unlimited)</label>
            <input type="number" name="storage_max_records" class="form-control" min="0"
                   value="<?= $sv('storage_max_records', 0) ?>">
          </div>
          <div class="col-md-6 d-flex align-items-center">
            <div class="form-check form-switch mt-3">
              <input class="form-check-input" type="checkbox" name="storage_dedup_enabled" id="chkDedup"
                     <?= $sb('storage_dedup_enabled') ? 'checked' : '' ?>>
              <label class="form-check-label" for="chkDedup">Enable Deduplication</label>
            </div>
          </div>
        </div>
      </div>

      <!-- Logging settings -->
      <div class="card mb-3">
        <div class="card-header border-secondary">Logging</div>
        <div class="card-body row g-3">
          <div class="col-md-4">
            <label class="form-label">Log Retention (days)</label>
            <input type="number" name="log_retention_days" class="form-control" min="1" max="3650"
                   value="<?= $sv('log_retention_days', 90) ?>">
          </div>
          <div class="col-md-4">
            <label class="form-label">Log Level</label>
            <select name="log_level" class="form-select">
              <?php foreach (['DEBUG','INFO','WARNING','ERROR'] as $lv): ?>
              <option value="<?= $lv ?>" <?= ($settings['log_level']['value']??'INFO')===$lv?'selected':'' ?>><?= $lv ?></option>
              <?php endforeach; ?>
            </select>
          </div>
          <div class="col-md-4">
            <label class="form-label">Records Per Page</label>
            <input type="number" name="dashboard_records_per_page" class="form-control" min="10" max="500"
                   value="<?= $sv('dashboard_records_per_page', 50) ?>">
          </div>
        </div>
      </div>

      <div class="d-flex gap-2">
        <button type="submit" class="btn btn-success">
          <i class="bi bi-check-lg me-1"></i>Save Settings
        </button>
      </div>
    </div>

    <!-- Right: DB info & tools -->
    <div class="col-md-4">
      <div class="card mb-3">
        <div class="card-header border-secondary">Database</div>
        <div class="card-body">
          <div class="mb-2 small">
            <span class="text-secondary">Host:</span> <strong><?= h(DB_HOST) ?>:<?= h(DB_PORT) ?></strong><br>
            <span class="text-secondary">Database:</span> <strong><?= h(DB_NAME) ?></strong>
          </div>
          <table class="table table-sm mb-3">
            <thead class="table-dark"><tr><th>Table</th><th class="text-end">Rows</th></tr></thead>
            <tbody>
              <?php foreach ($counts as $tbl => $cnt): ?>
              <tr>
                <td class="font-monospace small"><?= h($tbl) ?></td>
                <td class="text-end"><?= h(number_format($cnt)) ?></td>
              </tr>
              <?php endforeach; ?>
            </tbody>
          </table>
          <div class="d-grid gap-2">
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="purgeOldLogs()">
              <i class="bi bi-trash me-1"></i>Purge Old Logs
            </button>
            <button type="button" class="btn btn-sm btn-outline-warning" onclick="purgeRuns()">
              <i class="bi bi-trash me-1"></i>Purge Old Runs
            </button>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-header border-secondary">System Info</div>
        <div class="card-body small">
          <div class="d-flex justify-content-between mb-1">
            <span class="text-secondary">PHP</span><strong><?= h(PHP_VERSION) ?></strong>
          </div>
          <div class="d-flex justify-content-between mb-1">
            <span class="text-secondary">App Version</span><strong><?= h(APP_VERSION) ?></strong>
          </div>
          <div class="d-flex justify-content-between mb-1">
            <span class="text-secondary">Server Time</span><strong><?= h(date('Y-m-d H:i:s')) ?></strong>
          </div>
          <div class="d-flex justify-content-between mb-1">
            <span class="text-secondary">Timezone</span><strong><?= h(date_default_timezone_get()) ?></strong>
          </div>
        </div>
      </div>
    </div>

  </div>
</form>

<?php
$extra_js = <<<'JS'
<script>
function purgeOldLogs() {
  const days = prompt('Purge logs older than how many days?', '90');
  if (!days || isNaN(days)) return;
  apiPost(_api('api/logs.php?action=purge'), { days: parseInt(days) })
    .then(r => showToast(r.message ?? 'Done'))
    .catch(e => showToast(e.message, 'danger'));
}
function purgeRuns() {
  const days = prompt('Purge collection runs older than how many days?', '180');
  if (!days || isNaN(days)) return;
  apiPost(_api('api/runs.php?action=purge'), { days: parseInt(days) })
    .then(r => showToast(r.message ?? 'Done'))
    .catch(e => showToast(e.message, 'danger'));
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
