<?php
$page_title = 'Export Data';
$active_page = 'exports';
require_once __DIR__ . '/includes/header.php';

$states = db_all("SELECT DISTINCT state FROM raw_records WHERE state IS NOT NULL ORDER BY state");
$categories = db_all("SELECT DISTINCT category FROM raw_records WHERE category IS NOT NULL ORDER BY category");
$total_rec = (int)db_val("SELECT COUNT(*) FROM raw_records");
$gps_rec = (int)db_val("SELECT COUNT(*) FROM raw_records WHERE latitude IS NOT NULL");
?>

<div class="row g-3">
    <!-- Export form -->
    <div class="col-md-8">
        <div class="card mb-3">
            <div class="card-header border-secondary">
                <i class="fas fa-file-export me-2"></i>
                Export Records
            </div>
            <div class="card-body">
                <form id="exportForm" onsubmit="doExport(event)">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <label class="form-label">
                                <i class="fas fa-file-export me-1"></i>
                                Format
                            </label>
                            <select name="fmt" id="exportFmt" class="form-select">
                                <option value="csv">
                                    CSV
                                </option>
                                <option value="json">
                                    JSON
                                </option>
                                <option value="geojson">
                                    GeoJSON (GPS records only)
                                </option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">
                                <i class="fas fa-map-marker-alt me-1"></i>
                                State
                            </label>
                            <select name="state" id="exportState" class="form-select">
                                <option value="">All States</option>
                                <?php foreach ($states as $s): ?>
                                    <option value="<?= h($s['state']) ?>"><?= h($s['state']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">
                                <i class="fas fa-tag me-1"></i>
                                Category
                            </label>
                            <select name="category" id="exportCat" class="form-select">
                                <option value="">All Categories</option>
                                <?php foreach ($categories as $c): ?>
                                    <option value="<?= h($c['category']) ?>"><?= h($c['category']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">
                                <i class="fas fa-map-marker-alt me-1"></i>
                                GPS Only
                            </label>
                            <select name="gps" id="exportGps" class="form-select">
                                <option value="">All Records</option>
                                <option value="1">GPS Records Only</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">
                                <i class="fas fa-sort-numeric-up me-1"></i>
                                Max Rows (0 = all)
                            </label>
                            <input type="number" name="limit" id="exportLimit" class="form-control" value="0" min="0">
                        </div>
                        <div class="col-md-4 d-flex align-items-end">
                            <button type="submit" class="btn btn-success btn-sm">
                                <i class="fas fa-download me-1"></i>
                                Download Export
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>

        <!-- REST API reference -->
        <div class="card">
            <div class="card-header border-secondary">
                <i class="fas fa-code me-2"></i>
                REST API Reference
            </div>
            <div class="card-body p-0">
                <table class="table table-sm mb-0">
                    <thead class="table-dark">
                    <tr>
                        <th>
                            Method
                        </th>
                        <th>
                            Endpoint
                        </th>
                        <th>
                            Description
                        </th>
                    </tr>
                    </thead>
                    <tbody>
                    <?php
                    $apis = [['GET', 'api/records.php', 'List records (paginated)'], ['GET', 'api/records.php?id=N', 'Get single record by ID'], ['GET', 'api/records.php?action=export&fmt=csv', 'Export records as CSV'], ['GET', 'api/records.php?action=geojson', 'GeoJSON feature collection'], ['GET', 'api/sources.php', 'List all data sources'], ['POST', 'api/sources.php?action=run&id=ID', 'Trigger collection for source'], ['GET', 'api/stats.php', 'Dashboard statistics'], ['GET', 'api/stats.php?type=states', 'Record counts by state'], ['GET', 'api/stats.php?type=categories', 'Record counts by category'], ['GET', 'api/runs.php', 'List collection runs'], ['GET', 'api/logs.php', 'List collection logs'], ['POST', 'api/logs.php?action=purge', 'Purge old log entries'], ['GET', 'api/schedules.php', 'List schedules'],];
                    foreach ($apis as [$method, $endpoint, $desc]):
                        $badge = $method === 'GET' ? 'bg-info text-dark' : ($method === 'POST' ? 'bg-success' : 'bg-danger');
                        ?>
                        <tr>
                            <td>
                  <span class="badge <?= $badge ?>">
                      <?= $method ?>
                  </span>
                            </td>
                            <td>
                                <code>
                                    <?= h($endpoint) ?>
                                </code>
                            </td>
                            <td class="small text-secondary">
                                <?= h($desc) ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Summary sidebar -->
    <div class="col-md-4">
        <div class="card mb-3">
            <div class="card-header border-secondary">
                <i class="fas fa-info-circle me-2"></i>
                Dataset Summary
            </div>
            <div class="card-body">
                <div class="d-flex justify-content-between mb-2">
          <span class="text-secondary">
              <i class="fas fa-database me-1"></i>
              Total Records
          </span>
                    <strong><?= h(number_format($total_rec)) ?></strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
          <span class="text-secondary">
              <i class="fas fa-map-marker-alt me-1"></i>
              GPS Records
          </span>
                    <strong>
                        <?= h(number_format($gps_rec)) ?>
                    </strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
          <span class="text-secondary">
              <i class="fas fa-map-marker-alt me-1"></i>
              States
          </span>
                    <strong><?= h(count($states)) ?></strong>
                </div>
                <div class="d-flex justify-content-between mb-2">
          <span class="text-secondary">
              <i class="fas fa-tag me-1"></i>
              Categories
          </span>
                    <strong>
                        <?= h(count($categories)) ?>
                    </strong>
                </div>
            </div>
        </div>

        <div class="card mb-3">
            <div class="card-header border-secondary">
                <i class="fas fa-chart-bar me-2"></i>
                Records by State
            </div>
            <div class="card-body p-0">
                <table class="table table-sm mb-0">
                    <?php
                    $by_state = db_all("SELECT state, COUNT(*) AS cnt FROM raw_records WHERE state IS NOT NULL GROUP BY state ORDER BY cnt DESC LIMIT 15");
                    foreach ($by_state as $row): ?>
                        <tr>
                            <td>
                <span class="badge bg-secondary">
                    <?= h($row['state']) ?>
                </span>
                            </td>
                            <td class="text-end">
                                <?= h(number_format($row['cnt'])) ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </table>
            </div>
        </div>
    </div>
</div>

<?php
$extra_js = <<<'JS'
<script>
function doExport(e) {
  e.preventDefault();
  const fmt      = document.getElementById('exportFmt').value;
  const state    = document.getElementById('exportState').value;
  const cat      = document.getElementById('exportCat').value;
  const gps      = document.getElementById('exportGps').value;
  const limit    = document.getElementById('exportLimit').value;
  const action   = fmt === 'geojson' ? 'geojson' : 'export';
  const params   = new URLSearchParams({ action, fmt });
  if (state) params.set('state', state);
  if (cat)   params.set('category', cat);
  if (gps)   params.set('gps', gps);
  if (limit > 0) params.set('limit', limit);
  const ts = new Date().toISOString().slice(0,10);
  const filename = `cannabis_export_${ts}.${fmt}`;
  triggerDownload(_api('api/records.php?' + params), filename);
  showToast('Export started – file will download shortly', 'info');
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
