<?php
$page_title  = 'Dashboard';
$active_page = 'dashboard';
require_once __DIR__ . '/includes/header.php';

$stats = get_dashboard_stats();

// Recent runs (last 10)
$recent_runs = db_all("
    SELECT cr.id, cr.started_at, cr.completed_at, cr.status,
           cr.records_stored, cr.records_fetched, cr.duration_seconds, cr.triggered_by,
           ds.name AS source_name, ds.state, ds.category
    FROM   collection_runs cr
    JOIN   data_sources ds ON ds.id = cr.source_id
    ORDER  BY cr.started_at DESC
    LIMIT  10
");

// Records by state (top 10)
$by_state = db_all("
    SELECT state, COUNT(*) AS cnt
    FROM   raw_records
    WHERE  state IS NOT NULL
    GROUP  BY state
    ORDER  BY cnt DESC
    LIMIT  10
");

// Records by category
$by_cat = db_all("
    SELECT category, COUNT(*) AS cnt
    FROM   raw_records
    WHERE  category IS NOT NULL
    GROUP  BY category
    ORDER  BY cnt DESC
");

// Daily run counts (last 14 days)
$daily_runs = db_all("
    SELECT DATE(started_at) AS day,
           SUM(status='success') AS ok,
           SUM(status='failed')  AS fail
    FROM   collection_runs
    WHERE  started_at >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
    GROUP  BY day ORDER BY day
");
?>

<!-- Stat cards row -->
<div class="row g-3 mb-4">
  <?php
  $cards = [
    ['label'=>'Total Records',     'value'=>$stats['total_records'],   'icon'=>'fas fa-database',         'cls'=>'green'],
    ['label'=>'Active Sources',    'value'=>$stats['enabled_sources'],  'icon'=>'fas fa-database',         'cls'=>'green'],
    ['label'=>'GPS Records',       'value'=>$stats['gps_records'],     'icon'=>'fas fa-map-marker-alt',   'cls'=>'green'],
    ['label'=>'Runs Today',        'value'=>$stats['runs_today'],      'icon'=>'fas fa-calendar-day',       'cls'=>'yellow'],
    ['label'=>'Failed (24h)',      'value'=>$stats['failed_runs'],     'icon'=>'fas fa-exclamation-triangle', 'cls'=>'red'],
    ['label'=>'Active Schedules',  'value'=>$stats['total_schedules'], 'icon'=>'fas fa-clock',                'cls'=>'blue'],
  ];
  foreach ($cards as $c):
  ?>
  <div class="col-6 col-md-4 col-xl-2">
    <div class="card stat-card <?= $c['cls'] ?> h-100">
      <div class="card-body d-flex align-items-center gap-3">
        <div>
          <div class="stat-value">
              <?= h(number_format($c['value'])) ?>
          </div>
          <div class="stat-label mt-1">
              <i class="fas fa-tag me-1"></i>
              <?= h($c['label']) ?>
          </div>
        </div>
        <i class="fas fa-<?= $c['icon'] ?> fa-2x"></i>
      </div>
    </div>
  </div>
  <?php endforeach; ?>
</div>

<!-- Charts row -->
<div class="row g-3 mb-4">
  <div class="col-md-4">
    <div class="card h-100">
      <div class="card-header border-secondary">
          <i class="fas fa-database me-2 fa-2x"></i>
          Records by State
      </div>
      <div class="card-body">
          <div class="chart-wrap">
              <canvas id="chartState"></canvas>
          </div>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card h-100">
      <div class="card-header border-secondary">
          <i class="fas fa-tag me-2 fa-2x"></i>
          Records by Category
      </div>
      <div class="card-body">
          <div class="chart-wrap">
              <canvas id="chartCat"></canvas>
          </div>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card h-100">
      <div class="card-header border-secondary">
          <i class="fas fa-calendar-days me-2"></i>
          Daily Collection Runs (14 days)
      </div>
      <div class="card-body">
          <div class="chart-wrap">
              <canvas id="chartRuns"></canvas>
          </div>
      </div>
    </div>
  </div>
</div>

<!-- Recent runs table -->
<div class="card">
  <div class="card-header border-secondary d-flex align-items-center">
    <span>
        <i class="fas fa-history me-2"></i>
        Recent Collection Runs
    </span>
    <a href="logs.php" class="btn btn-sm btn-outline-secondary ms-auto">
        <i class="fas fa-list me-1"></i>
        View Logs
    </a>
  </div>
  <div class="card-body p-0">
    <?php if (empty($recent_runs)): ?>
    <div class="empty-state">
        <i class="fas fa-history fa-4x"></i>
        No runs yet. Set up a schedule or run a ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;ppppppppppp
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        manually.
    </div>
    <?php else: ?>
    <div class="table-responsive">
      <table class="table table-hover table-sm mb-0">
        <thead class="table-dark">
          <tr>
            <th>
                <i class="fas fa-hashtag me-2"></i>
                #
            </th>
              <th>
                  <i class="fas fa-database me-2"></i>
                  Source
              </th>
              <th>
                  <i class="fas fa-circle me-2"></i>
                  State
              </th>
              <th>
                  <i class="fas fa-circle me-2"></i>
                  Status
              </th>
            <th>
                <i class="fas fa-file-earmark-text me-2"></i>
                Fetched
            </th>
              <th>
                  <i class="fas fa-file-medical me-2"></i>
                  Stored
              </th>
              <th>
                  <i class="fas fa-clock me-2"></i>
                  Duration
              </th>
              <th>
                  <i class="fas fa-calendar-day me-2"></i>
                  Started
              </th>
              <th>
                  <i class="fas fa-user me-2"></i>
                  By
              </th>
          </tr>
        </thead>
        <tbody>
          <?php foreach ($recent_runs as $r): ?>
          <tr>
            <td class="text-secondary">
                <?= h($r['id']) ?>
            </td>
            <td class="fw-semibold">
                <?= h($r['source_name']) ?>
            </td>
            <td class="text-secondary">
                <?= h($r['state']) ?>
            </td>
            <td class="text-secondary">
                <?= status_badge($r['status']) ?>
            </td>
            <td title="<?= h(number_format($r['records_fetched'])) ?>">
                <?= h(number_format($r['records_fetched'])) ?>
            </td>
            <td title="<?= h(number_format($r['records_stored'])) ?>">
                <?= h(number_format($r['records_stored'])) ?>
            </td>
            <td title="<?= h(fmt_duration($r['duration_seconds'])) ?>">
                <?= h(fmt_duration($r['duration_seconds'])) ?>
            </td>
            <td title="<?= h($r['started_at']) ?>">
                <?= h(fmt_date($r['started_at'])) ?>
            </td>
            <td class="text-secondary">
                <span class="badge bg-secondary">
                    <?= h($r['triggered_by']) ?>
                </span>
            </td>
          </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <?php endif; ?>
  </div>
</div>

<?php
$stateLabels = json_encode(array_column($by_state, 'state'));
$stateCounts = json_encode(array_column($by_state, 'cnt'));
$catLabels   = json_encode(array_column($by_cat, 'category'));
$catCounts   = json_encode(array_column($by_cat, 'cnt'));
$runDays     = json_encode(array_column($daily_runs, 'day'));
$runOk       = json_encode(array_column($daily_runs, 'ok'));
$runFail     = json_encode(array_column($daily_runs, 'fail'));

$extra_js = <<<JS
<script>
const greens = ['#198754','#20c997','#0d6efd','#6610f2','#d63384','#ffc107','#0dcaf0','#fd7e14','#6c757d','#adb5bd'];
const mkBar  = (id, labels, data, color) => new Chart(document.getElementById(id), {
  type: 'bar',
  data: { labels, datasets: [{ data, backgroundColor: color ?? greens, borderRadius: 4 }] },
  options: { plugins:{legend:{display:false}}, scales:{ y:{beginAtZero:true}, x:{ ticks:{color:'#aaa'} }, y0:{ticks:{color:'#aaa'}} }, responsive:true, maintainAspectRatio:false }
});
mkBar('chartState', $stateLabels, $stateCounts);
mkBar('chartCat',   $catLabels,   $catCounts);
new Chart(document.getElementById('chartRuns'), {
  type: 'bar',
  data: {
    labels: $runDays,
    datasets: [
      { label:'Success', data: $runOk,   backgroundColor:'#198754', borderRadius:4 },
      { label:'Failed',  data: $runFail, backgroundColor:'#dc3545', borderRadius:4 }
    ]
  },
  options: { plugins:{legend:{labels:{color:'#aaa'}}}, scales:{ x:{stacked:true,ticks:{color:'#aaa'}}, y:{stacked:true,beginAtZero:true,ticks:{color:'#aaa'}} }, responsive:true, maintainAspectRatio:false }
});
</script>
JS;

require_once __DIR__ . '/includes/footer.php';
