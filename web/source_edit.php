<?php
require_once __DIR__ . '/includes/functions.php';

$id  = get_int('id');
$src = $id ? db_row("SELECT * FROM data_sources WHERE id=?", [$id]) : null;
$is_new = !$src;

$page_title  = $is_new ? 'Add Source' : 'Edit Source: ' . ($src['name'] ?? '');
$active_page = 'sources';

// Handle POST
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_verify();

    $data = [
        'source_id'       => post_str('source_id'),
        'name'            => post_str('name'),
        'description'     => post_str('description'),
        'state'           => post_str('state'),
        'agency'          => post_str('agency'),
        'category'        => post_str('category'),
        'subcategory'     => post_str('subcategory'),
        'format'          => post_str('format'),
        'url'             => post_str('url'),
        'discovery_url'   => post_str('discovery_url'),
        'website'         => post_str('website'),
        'enabled'         => isset($_POST['enabled']) ? 1 : 0,
        'api_key_required'=> isset($_POST['api_key_required']) ? 1 : 0,
        'api_key_env'     => post_str('api_key_env'),
        'notes'           => post_str('notes'),
        'rate_limit_rpm'  => max(1, post_int('rate_limit_rpm', 60)),
        'timeout'         => max(5, post_int('timeout', 60)),
    ];

    // JSON fields
    foreach (['params','headers','field_mapping','tags','pagination'] as $jf) {
        $raw = trim(post_str($jf));
        if ($raw === '') { $data[$jf] = null; continue; }
        $decoded = json_decode($raw, true);
        $data[$jf] = json_last_error() === JSON_ERROR_NONE ? $raw : null;
    }

    if (empty($data['source_id']) || empty($data['name']) || empty($data['state']) ||
        empty($data['category']) || empty($data['format'])) {
        $_SESSION['flash'][] = ['type'=>'danger','msg'=>'Source ID, Name, State, Category and Format are required.'];
    } else {
        if ($is_new) {
            $cols = implode(', ', array_keys($data));
            $phs  = implode(', ', array_fill(0, count($data), '?'));
            $newId = db_exec("INSERT INTO data_sources ($cols) VALUES ($phs)", array_values($data));
            $_SESSION['flash'][] = ['type'=>'success','msg'=>'Source created.'];
            redirect('source_edit.php?id=' . $newId);
        } else {
            $sets = implode(', ', array_map(fn($k) => "$k=?", array_keys($data)));
            db_exec("UPDATE data_sources SET $sets, updated_at=NOW() WHERE id=?",
                    array_merge(array_values($data), [$id]));
            $_SESSION['flash'][] = ['type'=>'success','msg'=>'Source updated.'];
            redirect('source_edit.php?id=' . $id);
        }
    }
    $src = $src ? array_merge($src, $data) : $data;
}

require_once __DIR__ . '/includes/header.php';
$src ??= [];   // treat null as empty array so $v() never warns on a new-form GET
$v = fn($k) => h($src[$k] ?? '');
?>

<div class="d-flex align-items-center mb-3 gap-2">
  <a href="sources.php" class="btn btn-sm btn-outline-secondary"><i class="bi bi-arrow-left me-1"></i>Back</a>
  <h5 class="mb-0"><?= $is_new ? 'Add New Source' : 'Edit Source' ?></h5>
</div>

<form method="post">
  <?= csrf_field() ?>
  <div class="row g-3">

    <!-- Left column -->
    <div class="col-md-8">
      <div class="card mb-3">
        <div class="card-header border-secondary">Basic Info</div>
        <div class="card-body row g-3">
          <div class="col-md-6">
            <label class="form-label">Source ID <span class="text-danger">*</span></label>
            <input type="text" name="source_id" class="form-control" required
                   value="<?= $v('source_id') ?>" <?= !$is_new?'readonly':'' ?>
                   placeholder="e.g. ca_dcc_licenses">
            <div class="form-text">Unique snake_case identifier. Cannot be changed after creation.</div>
          </div>
          <div class="col-md-6">
            <label class="form-label">Display Name <span class="text-danger">*</span></label>
            <input type="text" name="name" class="form-control" required value="<?= $v('name') ?>">
          </div>
          <div class="col-12">
            <label class="form-label">Description</label>
            <textarea name="description" class="form-control" rows="2"><?= $v('description') ?></textarea>
          </div>
          <div class="col-md-4">
            <label class="form-label">State <span class="text-danger">*</span></label>
            <input type="text" name="state" class="form-control" required value="<?= $v('state') ?>"
                   placeholder="CA" maxlength="20">
          </div>
          <div class="col-md-4">
            <label class="form-label">Category <span class="text-danger">*</span></label>
            <input type="text" name="category" class="form-control" required value="<?= $v('category') ?>"
                   placeholder="licenses" list="category-list">
            <datalist id="category-list">
              <?php foreach (get_distinct_categories() as $c): ?>
              <option value="<?= h($c['category']) ?>">
              <?php endforeach; ?>
            </datalist>
          </div>
          <div class="col-md-4">
            <label class="form-label">Subcategory</label>
            <input type="text" name="subcategory" class="form-control" value="<?= $v('subcategory') ?>">
          </div>
          <div class="col-md-6">
            <label class="form-label">Agency</label>
            <input type="text" name="agency" class="form-control" value="<?= $v('agency') ?>">
          </div>
          <div class="col-md-6">
            <label class="form-label">Format <span class="text-danger">*</span></label>
            <select name="format" class="form-select" required>
              <?php foreach (['soda','csv','json','geojson','xml'] as $fmt): ?>
              <option value="<?= $fmt ?>" <?= ($src['format']??'')===$fmt?'selected':'' ?>><?= strtoupper($fmt) ?></option>
              <?php endforeach; ?>
            </select>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-header border-secondary">URLs</div>
        <div class="card-body row g-3">
          <div class="col-12">
            <label class="form-label">Data URL</label>
            <input type="url" name="url" class="form-control" value="<?= $v('url') ?>" placeholder="https://…">
          </div>
          <div class="col-md-6">
            <label class="form-label">Discovery URL</label>
            <input type="url" name="discovery_url" class="form-control" value="<?= $v('discovery_url') ?>">
          </div>
          <div class="col-md-6">
            <label class="form-label">Website</label>
            <input type="url" name="website" class="form-control" value="<?= $v('website') ?>">
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-header border-secondary">Advanced (JSON)</div>
        <div class="card-body row g-3">
          <?php
          $json_fields = [
            'params'       => 'Default Query Params',
            'headers'      => 'Custom Headers',
            'field_mapping'=> 'Field Mapping',
            'tags'         => 'Tags (array)',
            'pagination'   => 'Pagination Config',
          ];
          foreach ($json_fields as $jf => $jlabel): ?>
          <div class="col-md-6">
            <label class="form-label"><?= h($jlabel) ?></label>
            <textarea name="<?= $jf ?>" class="form-control font-monospace" rows="3"
                      style="font-size:.78rem"><?= h($src[$jf] ?? '') ?></textarea>
          </div>
          <?php endforeach; ?>
          <div class="col-12">
            <label class="form-label">Notes</label>
            <textarea name="notes" class="form-control" rows="2"><?= $v('notes') ?></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Right column -->
    <div class="col-md-4">
      <div class="card mb-3">
        <div class="card-header border-secondary">Settings</div>
        <div class="card-body">
          <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" name="enabled" id="chkEnabled"
                   <?= ($src['enabled']??1) ? 'checked' : '' ?>>
            <label class="form-check-label" for="chkEnabled">Enabled</label>
          </div>
          <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" name="api_key_required" id="chkApiKey"
                   <?= ($src['api_key_required']??0) ? 'checked' : '' ?>>
            <label class="form-check-label" for="chkApiKey">API Key Required</label>
          </div>
          <div class="mb-3">
            <label class="form-label">API Key Env Var</label>
            <input type="text" name="api_key_env" class="form-control" value="<?= $v('api_key_env') ?>"
                   placeholder="MY_API_KEY">
          </div>
          <div class="mb-3">
            <label class="form-label">Rate Limit (req/min)</label>
            <input type="number" name="rate_limit_rpm" class="form-control" min="1" max="3600"
                   value="<?= h($src['rate_limit_rpm'] ?? 60) ?>">
          </div>
          <div class="mb-3">
            <label class="form-label">Timeout (seconds)</label>
            <input type="number" name="timeout" class="form-control" min="5" max="600"
                   value="<?= h($src['timeout'] ?? 60) ?>">
          </div>
        </div>
      </div>

      <?php if (!$is_new): ?>
      <div class="card mb-3">
        <div class="card-header border-secondary">Statistics</div>
        <div class="card-body">
          <?php
          $rc  = (int)db_val("SELECT COUNT(*) FROM raw_records WHERE source_id=?", [$id]);
          $gps = (int)db_val("SELECT COUNT(*) FROM raw_records WHERE source_id=? AND latitude IS NOT NULL", [$id]);
          $runs= (int)db_val("SELECT COUNT(*) FROM collection_runs WHERE source_id=?", [$id]);
          $last= db_val("SELECT MAX(started_at) FROM collection_runs WHERE source_id=?", [$id]);
          ?>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-secondary">Records</span>
            <strong><?= h(number_format($rc)) ?></strong>
          </div>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-secondary">GPS Records</span>
            <strong><?= h(number_format($gps)) ?></strong>
          </div>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-secondary">Total Runs</span>
            <strong><?= h(number_format($runs)) ?></strong>
          </div>
          <div class="d-flex justify-content-between mb-2">
            <span class="text-secondary">Last Run</span>
            <strong><?= $last ? h(fmt_date($last)) : '–' ?></strong>
          </div>
        </div>
      </div>
      <?php endif; ?>

      <div class="d-grid gap-2">
        <button type="submit" class="btn btn-success">
          <i class="bi bi-check-lg me-1"></i><?= $is_new ? 'Create Source' : 'Save Changes' ?>
        </button>
        <a href="sources.php" class="btn btn-outline-secondary">Cancel</a>
        <?php if (!$is_new): ?>
        <button type="button" class="btn btn-outline-success"
                onclick="runSource('<?= h($src['source_id'] ?? '') ?>','<?= h(addslashes($src['name'] ?? '')) ?>')">
          <i class="bi bi-play-fill me-1"></i>Run Now
        </button>
        <?php endif; ?>
      </div>
    </div>

  </div>
</form>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
