<?php
$page_title  = 'Browse Records';
$active_page = 'data';
require_once __DIR__ . '/includes/header.php';

// Filters
$f_state    = get_str('state');
$f_category = get_str('category');
$f_source   = get_str('source');
$f_status   = get_str('license_status');
$f_gps      = get_str('gps');
$f_search   = get_str('q');
$page       = max(1, get_int('page', 1));
$per_page   = (int)get_setting('dashboard_records_per_page', DEFAULT_PAGE_SIZE);

// Build WHERE
$where = []; $params = [];
if ($f_state)    { $where[] = 'r.state = ?';    $params[] = $f_state; }
if ($f_category) { $where[] = 'r.category = ?'; $params[] = $f_category; }
if ($f_status)   { $where[] = 'r.license_status = ?'; $params[] = $f_status; }
if ($f_gps === '1') { $where[] = 'r.latitude IS NOT NULL AND r.longitude IS NOT NULL'; }
if ($f_source) {
    $dsRow = db_row("SELECT id FROM data_sources WHERE source_id=?", [$f_source]);
    if ($dsRow) { $where[] = 'r.source_id = ?'; $params[] = $dsRow['id']; }
}
if ($f_search) {
    $where[] = '(r.name LIKE ? OR r.license_number LIKE ? OR r.city LIKE ? OR r.county LIKE ?)';
    $s = "%$f_search%"; $params = array_merge($params, [$s,$s,$s,$s]);
}
$wclause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

$total = (int)db_val("SELECT COUNT(*) FROM raw_records r $wclause", $params);
[$limit, $offset] = limit_offset($page, $per_page);
$pg = paginate($total, $page, $per_page);

$records = db_all("
    SELECT r.id, r.state, r.category, r.name, r.license_number, r.license_type,
           r.license_status, r.city, r.county, r.zip_code, r.address,
           r.latitude, r.longitude, r.phone, r.email, r.website,
           r.record_date, r.license_date, r.expiry_date, r.created_at,
           ds.name AS source_name, ds.source_id
    FROM   raw_records r
    JOIN   data_sources ds ON ds.id = r.source_id
    $wclause
    ORDER  BY r.created_at DESC
    LIMIT  ? OFFSET ?
", array_merge($params, [$limit, $offset]));

$states     = db_all("SELECT DISTINCT state FROM raw_records WHERE state IS NOT NULL ORDER BY state");
$categories = db_all("SELECT DISTINCT category FROM raw_records WHERE category IS NOT NULL ORDER BY category");
$statuses   = db_all("SELECT DISTINCT license_status FROM raw_records WHERE license_status IS NOT NULL ORDER BY license_status");
$sources    = get_all_sources();
?>

<!-- Filter bar -->
<form method="get" class="filter-bar p-3 mb-4">
  <div class="row g-2 align-items-end">
    <div class="col-md-3">
      <label class="form-label small mb-1">
          <i class="fas fa-search me-1"></i>
          Search
      </label>
      <input type="text" name="q" class="form-control form-control-sm" placeholder="Name, license #, city…" value="<?= h($f_search) ?>">
    </div>
    <div class="col-md-2">
      <label class="form-label small mb-1">
          <i class="fas fa-flag me-1"></i>
          State
      </label>
      <select name="state" class="form-select form-select-sm">
        <option value="" <?= $f_state===''?'selected':'' ?>>
            All States
        </option>
        <?php foreach ($states as $s): ?>
        <option value="<?= h($s['state']) ?>" <?= $f_state===$s['state']?'selected':'' ?>><?= h($s['state']) ?></option>
        <?php endforeach; ?>
      </select>
    </div>
    <div class="col-md-2">
      <label class="form-label small mb-1">
          <i class="fas fa-tag me-1"></i>
          Category
      </label>
      <select name="category" class="form-select form-select-sm">
        <option value="" <?= $f_category===''?'selected':'' ?>>
            All Categories
        </option>
        <?php foreach ($categories as $c): ?>
        <option value="<?= h($c['category']) ?>" <?= $f_category===$c['category']?'selected':'' ?>><?= h($c['category']) ?></option>
        <?php endforeach; ?>
      </select>
    </div>
    <div class="col-md-2">
      <label class="form-label small mb-1">
          <i class="fas fa-database me-1"></i>
          License Status
      </label>
      <select name="license_status" class="form-select form-select-sm">
        <option value="" <?= $f_status===''?'selected':'' ?>>
            All Statuses
        </option>
        <?php foreach ($statuses as $st): ?>
        <option value="<?= h($st['license_status']) ?>" <?= $f_status===$st['license_status']?'selected':'' ?>><?= h($st['license_status']) ?></option>
        <?php endforeach; ?>
      </select>
    </div>
    <div class="col-md-1">
      <label class="form-label small mb-1">
          <i class="fas fa-map-marker-alt me-1"></i>
          GPS Only
      </label>
      <select name="gps" class="form-select form-select-sm">
        <option value="" <?= $f_gps===''?'selected':'' ?>>
            All
        </option>
        <option value="1" <?= $f_gps==='1'?'selected':'' ?>>
            GPS Only
        </option>
      </select>
    </div>
    <div class="col-md-1">
      <button type="submit" class="btn btn-sm btn-success">
          <i class="fas fa-filter me-1"></i>
          Filter
      </button>
    </div>
    <?php if ($f_state||$f_category||$f_status||$f_gps||$f_search||$f_source): ?>
    <div class="col-md-1">
      <a href="data.php" class="btn btn-sm btn-outline-secondary">
          <i class="fas fa-times me-1"></i>
          Clear
      </a>
    </div>
    <?php endif; ?>
  </div>
</form>

<!-- Toolbar -->
<div class="d-flex align-items-center mb-3 gap-2 flex-wrap">
  <span class="text-secondary small">
      <?= h(number_format($total)) ?>
      record
      <?= $total!==1?'s':'' ?>
  </span>
  <a href="map.php?<?= h(http_build_query(array_filter(['state'=>$f_state,'category'=>$f_category]))) ?>"
     class="btn btn-sm btn-outline-info ms-auto">
    <i class="fas fa-map-marked-alt me-1"></i>
      Map View
  </a>
  <div class="dropdown">
    <button class="btn btn-sm btn-outline-success dropdown-toggle" data-bs-toggle="dropdown">
      <i class="fas fa-file-export me-1"></i>
        Export
    </button>
    <ul class="dropdown-menu dropdown-menu-end">
      <?php foreach (['csv','json','geojson'] as $fmt):
        $q = http_build_query(array_filter(['state'=>$f_state,'category'=>$f_category,'q'=>$f_search,'fmt'=>$fmt])); ?>
      <li>
          <a class="dropdown-item" href="<?= WEB_BASE ?>
          api/records.php?action=export&
          <?= h($q) ?>">
        <?= strtoupper($fmt) ?>
          </a>
      </li>
      <?php endforeach; ?>
    </ul>
  </div>
</div>

<!-- Table -->
<?php if (empty($records)): ?>
<div class="empty-state">
    <i class="fas fa-search fa-4x text-secondary"></i>
    No records match your filters.
</div>
<?php else: ?>
<div class="card">
  <div class="card-body p-0">
    <div class="table-responsive">
      <table class="table table-hover table-sm mb-0">
        <thead class="table-dark">
          <tr>
            <th style="min-width: 200px;">
                <i class="fas fa-search me-1"></i>
                Name
            </th>
              <th style="min-width: 120px;">
                  <i class="fas fa-hashtag me-1"></i>
                  License #
              </th>
              <th style="min-width: 150px;">
                  <i class="fas fa-tag me-1"></i>
                  Type
              </th>
              <th style="min-width: 120px;">
                  <i class="fas fa-circle me-1"></i>
                  Status
              </th>
            <th style="min-width: 150px;">
                <i class="fas fa-flag me-1"></i>
                City
            </th>
              <th style="min-width: 100px;">
                  <i class="fas fa-flag me-1"></i>
                  State
              </th>
              <th style="min-width: 150px;">
                  <i class="fas fa-tag me-1"></i>
                  Category
              </th>
              <th style="min-width: 150px;">
                  <i class="fas fa-database me-1"></i>
                  Source
              </th>
            <th style="min-width: 80px; text-align: center;">
                <i class="fas fa-map-marker-alt me-1"></i>
                GPS
            </th>
              <th style="min-width: 120px;">
                  <i class="fas fa-calendar-day me-1"></i>
                  Date
              </th>
              <th>

              </th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($records as $rec): ?>
          <tr class="cursor-pointer" onclick="showRecord(<?= h($rec['id']) ?>)">
            <td class="fw-semibold">
                <?= h($rec['name'] ?: '–') ?>
            </td>
            <td class="font-monospace small">
                <?= h($rec['license_number'] ?: '–') ?>
            </td>
            <td class="small">
                <?= h($rec['license_type'] ?: '–') ?>
            </td>
            <td>
              <?php if ($rec['license_status']): ?>
              <span class="badge bg-secondary">
                  <?= h($rec['license_status']) ?>
              </span>
              <?php else: ?>–<?php endif; ?>
            </td>
            <td>
                <?= h($rec['city'] ?: '–') ?>
            </td>
            <td>
                <span class="badge bg-secondary">
                    <?= h($rec['state'] ?: '–') ?>
                </span>
            </td>
            <td>
                <?= h($rec['category'] ?: '–') ?>
            </td>
            <td class="small text-secondary">
                <?= h($rec['source_name']) ?>
            </td>
            <td>
                <?= ($rec['latitude'] && $rec['longitude'])
              ? '<i class="fas fa-check text-success" title="' . h($rec['latitude']) . ',' . h($rec['longitude']) . '"></i>'
              : '<span class="text-secondary">–</span>' ?></td>
            <td class="small text-secondary">
                <?= $rec['record_date'] ? h(fmt_date($rec['record_date'], 'Y-m-d')) : '–' ?>
            </td>
            <td onclick="event.stopPropagation()">
              <button class="btn btn-sm btn-outline-secondary py-0" onclick="showRecord(<?= h($rec['id']) ?>)">
                <i class="fas fa-eye me-1"></i>
                 View
              </button>
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
    <?php
    $maxPages = $pg['pages'];
    $start = max(1, $page - 4); $end = min($maxPages, $page + 4);
    if ($start > 1): $q = http_build_query(array_merge($_GET,['page'=>1])); ?>
    <li class="page-item">
        <a class="page-link" href="?<?= h($q) ?>">
            1
        </a>
    </li>
    <?php if ($start > 2): ?>
            <li class="page-item disabled">
                <span class="page-link">
                    …
                </span>
            </li>
        <?php endif; ?>
    <?php endif; ?>
    <?php for ($i=$start;$i<=$end;$i++): $q=http_build_query(array_merge($_GET,['page'=>$i])); ?>
    <li class="page-item <?= $i===$page?'active':'' ?>">
        <a class="page-link" href="?<?= h($q) ?>">
            <?= $i ?>
        </a>
    </li>
    <?php endfor; ?>
    <?php if ($end < $maxPages): ?>
    <?php if ($end < $maxPages - 1): ?>
            <li class="page-item disabled">
                <span class="page-link">
                    …
                </span>
            </li>
        <?php endif; ?>
    <?php $q=http_build_query(array_merge($_GET,['page'=>$maxPages])); ?>
    <li class="page-item">
        <a class="page-link" href="?<?= h($q) ?>">
            <?= $maxPages ?>
        </a>
    </li>
    <?php endif; ?>
  </ul>
</nav>
<?php endif; ?>
<?php endif; ?>

<!-- Record detail modal -->
<div class="modal fade" id="recordModal" tabindex="-1">
  <div class="modal-dialog modal-xl modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header border-secondary">
        <h5 class="modal-title" id="recordModalTitle">
            <i class="fas fa-search me-1"></i>
            Record Details
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="recordModalBody">
        <div class="text-center py-4">
            <div class="spinner-border text-success"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<?php
$extra_js = <<<'JS'
<script>
function showRecord(id) {
  const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('recordModal'));
  const body  = document.getElementById('recordModalBody');
  body.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-success"></div></div>';
  modal.show();
  apiGet(_api('api/records.php?id=' + id))
    .then(r => {
      const rec = r.record ?? r;
      let html = '<div class="row g-3">';
      const fields = [
        ['Name', rec.name], ['License #', rec.license_number], ['License Type', rec.license_type],
        ['License Status', rec.license_status], ['Address', rec.address], ['City', rec.city],
        ['County', rec.county], ['ZIP', rec.zip_code], ['State', rec.state], ['Category', rec.category],
        ['Phone', rec.phone], ['Email', rec.email ? `<a href="mailto:${escHtml(rec.email)}">${escHtml(rec.email)}</a>` : null, true],
        ['Website', rec.website ? `<a href="${escHtml(rec.website)}" target="_blank" rel="noopener">${escHtml(rec.website)}</a>` : null, true],
        ['GPS', (rec.latitude && rec.longitude) ? `${rec.latitude}, ${rec.longitude}` : null],
        ['Record Date', rec.record_date], ['License Date', rec.license_date], ['Expiry Date', rec.expiry_date],
        ['Source', rec.source_name], ['Created', rec.created_at],
      ];
      fields.forEach(([k, v, raw]) => {
        if (!v) return;
        html += `<div class="col-md-4"><dt class="text-secondary small">${escHtml(k)}</dt><dd>${raw ? v : escHtml(v)}</dd></div>`;
      });
      html += '</div>';
      if (rec.record_data) {
        html += `<hr class="border-secondary"><h6>Raw Data</h6><pre class="json-pre p-3">${escHtml(JSON.stringify(rec.record_data, null, 2))}</pre>`;
      }
      document.getElementById('recordModalTitle').textContent = rec.name ?? ('Record #' + rec.id);
      body.innerHTML = html;
    })
    .catch(e => { body.innerHTML = `<div class="alert alert-danger">${escHtml(e.message)}</div>`; });
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
