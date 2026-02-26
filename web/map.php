<?php
$page_title  = 'Map View';
$active_page = 'map';
require_once __DIR__ . '/includes/header.php';

$f_state    = get_str('state');
$f_category = get_str('category');

$states     = db_all("SELECT DISTINCT state FROM raw_records WHERE latitude IS NOT NULL ORDER BY state");
$categories = db_all("SELECT DISTINCT category FROM raw_records WHERE latitude IS NOT NULL ORDER BY category");
$gps_count  = (int)db_val("SELECT COUNT(*) FROM raw_records WHERE latitude IS NOT NULL AND longitude IS NOT NULL");
?>

<div class="d-flex align-items-center mb-3 gap-3 flex-wrap">
  <span class="text-secondary small"><?= h(number_format($gps_count)) ?> GPS-tagged records</span>

  <!-- Inline filters (passed to JS for API call) -->
  <div class="d-flex gap-2 ms-auto">
    <select id="filterState" class="form-select form-select-sm" style="width:auto">
      <option value="">All States</option>
      <?php foreach ($states as $s): ?>
      <option value="<?= h($s['state']) ?>" <?= $f_state===$s['state']?'selected':'' ?>><?= h($s['state']) ?></option>
      <?php endforeach; ?>
    </select>
    <select id="filterCat" class="form-select form-select-sm" style="width:auto">
      <option value="">All Categories</option>
      <?php foreach ($categories as $c): ?>
      <option value="<?= h($c['category']) ?>" <?= $f_category===$c['category']?'selected':'' ?>><?= h($c['category']) ?></option>
      <?php endforeach; ?>
    </select>
    <button class="btn btn-sm btn-success" onclick="loadMap()">Apply</button>
  </div>
</div>

<!-- Map -->
<div id="map"></div>

<!-- Loading -->
<div id="mapLoading" class="text-center py-3" style="display:none">
  <div class="spinner-border text-success me-2"></div>Loading map data…
</div>

<!-- Category legend -->
<div id="mapLegend" class="mt-2 d-flex gap-2 flex-wrap" style="font-size:.8rem"></div>

<?php
$initState = json_encode($f_state);
$initCat   = json_encode($f_category);

$extra_js = <<<JS
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
<script>
const CAT_COLORS = [
  '#198754','#0d6efd','#ffc107','#dc3545','#20c997','#6610f2','#d63384','#fd7e14','#6c757d','#0dcaf0'
];
let map, markers, catColorMap = {};

document.addEventListener('DOMContentLoaded', () => {
  map = L.map('map').setView([39.5, -98.35], 4);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; Carto', maxZoom: 19
  }).addTo(map);
  markers = L.markerClusterGroup({ chunkedLoading: true });
  map.addLayer(markers);
  loadMap();
});

function loadMap() {
  const state = document.getElementById('filterState').value;
  const cat   = document.getElementById('filterCat').value;
  const params = new URLSearchParams();
  if (state) params.set('state', state);
  if (cat)   params.set('category', cat);

  document.getElementById('mapLoading').style.display = '';
  markers.clearLayers();

  fetch(_api('api/records.php?action=geojson&' + params))
    .then(r => r.json())
    .then(data => {
      document.getElementById('mapLoading').style.display = 'none';
      const features = data.features ?? [];
      // Build category color map
      const cats = [...new Set(features.map(f => f.properties.category))].filter(Boolean);
      cats.forEach((c,i) => catColorMap[c] = CAT_COLORS[i % CAT_COLORS.length]);

      features.forEach(f => {
        const [lng, lat] = f.geometry.coordinates;
        const p = f.properties;
        const color = catColorMap[p.category] ?? '#aaa';
        const icon = L.divIcon({
          className: '',
          html: `<div style="width:10px;height:10px;border-radius:50%;background:\${color};border:1px solid rgba(255,255,255,.5)"></div>`,
          iconSize: [10,10], iconAnchor: [5,5]
        });
        const popup = `<strong>\${escHtml(p.name??'')}</strong><br>
          \${escHtml(p.license_number??'')} · \${escHtml(p.license_status??'')}<br>
          \${escHtml(p.address??'')} \${escHtml(p.city??'')} \${escHtml(p.state??'')}<br>
          <em>\${escHtml(p.category??'')}</em>`;
        markers.addLayer(L.marker([lat, lng], {icon}).bindPopup(popup));
      });

      // Legend
      const leg = document.getElementById('mapLegend');
      leg.innerHTML = Object.entries(catColorMap).map(([c,clr]) =>
        `<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:\${clr};margin-right:4px"></span>\${escHtml(c)}</span>`
      ).join('');
    })
    .catch(e => {
      document.getElementById('mapLoading').style.display = 'none';
      showToast('Map error: ' + e.message, 'danger');
    });
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
