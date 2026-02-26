<?php
$page_title  = 'Script Manager';
$active_page = 'scripts';
require_once __DIR__ . '/includes/header.php';

// Allowed script directories (relative to APP_ROOT)
$allowed_dirs = ['scripts', 'src', 'src/collectors', 'src/storage', 'src/utils'];

// Collect all .py files from allowed dirs
$files = [];
foreach ($allowed_dirs as $rel) {
    $abs = APP_ROOT . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $rel);
    if (!is_dir($abs)) continue;
    $items = glob($abs . DIRECTORY_SEPARATOR . '*.py');
    if (!$items) continue;
    foreach ($items as $path) {
        $files[] = [
            'dir'      => $rel,
            'filename' => basename($path),
            'path'     => $path,
            'rel_path' => $rel . '/' . basename($path),
            'size'     => filesize($path),
            'mtime'    => filemtime($path),
        ];
    }
}

// Sort by directory then filename
usort($files, fn($a, $b) => ($a['dir'] <=> $b['dir']) ?: ($a['filename'] <=> $b['filename']));

// Group by directory
$grouped = [];
foreach ($files as $f) {
    $grouped[$f['dir']][] = $f;
}

function fmt_bytes(int $b): string {
    if ($b < 1024)       return $b . ' B';
    if ($b < 1048576)    return round($b / 1024, 1) . ' KB';
    return round($b / 1048576, 2) . ' MB';
}
?>

<div class="d-flex justify-content-between align-items-center mb-3">
  <div class="text-secondary small">
    <?= count($files) ?> script<?= count($files) !== 1 ? 's' : '' ?> found across
    <?= count($grouped) ?> director<?= count($grouped) !== 1 ? 'ies' : 'y' ?>
  </div>
  <button class="btn btn-success btn-sm" onclick="showNewScriptModal()">
    <i class="bi bi-plus-circle me-1"></i>New Script
  </button>
</div>

<?php if (empty($files)): ?>
<div class="empty-state">
  <i class="bi bi-file-code"></i>
  <p>No Python scripts found.</p>
  <p class="small">Scripts are discovered from: <code><?= h(implode(', ', $allowed_dirs)) ?></code></p>
  <button class="btn btn-success mt-2" onclick="showNewScriptModal()">
    <i class="bi bi-plus-circle me-1"></i>Create First Script
  </button>
</div>
<?php else: ?>

<?php foreach ($grouped as $dir => $dir_files): ?>
<div class="card mb-3">
  <div class="card-header border-secondary d-flex align-items-center gap-2">
    <i class="bi bi-folder2-open text-warning"></i>
    <code class="text-warning"><?= h($dir) ?>/</code>
    <span class="badge bg-secondary ms-auto"><?= count($dir_files) ?> file<?= count($dir_files) !== 1 ? 's' : '' ?></span>
  </div>
  <div class="card-body p-0">
    <table class="table table-sm table-hover mb-0">
      <thead class="table-dark">
        <tr>
          <th>Filename</th>
          <th>Size</th>
          <th>Modified</th>
          <th class="text-end">Actions</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($dir_files as $f): ?>
        <tr>
          <td>
            <i class="bi bi-filetype-py text-primary me-1"></i>
            <code><?= h($f['filename']) ?></code>
          </td>
          <td class="text-secondary small"><?= h(fmt_bytes($f['size'])) ?></td>
          <td class="text-secondary small"><?= date('Y-m-d H:i', $f['mtime']) ?></td>
          <td class="text-end">
            <a href="<?= WEB_BASE ?>script_edit.php?path=<?= urlencode($f['rel_path']) ?>"
               class="btn btn-sm btn-outline-primary me-1">
              <i class="bi bi-pencil"></i> Edit
            </a>
            <button class="btn btn-sm btn-outline-success me-1"
                    onclick="runScript(<?= h(json_encode($f['rel_path'])) ?>, <?= h(json_encode($f['filename'])) ?>)">
              <i class="bi bi-play-fill"></i> Run
            </button>
            <button class="btn btn-sm btn-outline-danger"
                    onclick="deleteScript(<?= h(json_encode($f['rel_path'])) ?>, <?= h(json_encode($f['filename'])) ?>)">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>
</div>
<?php endforeach; ?>
<?php endif; ?>

<!-- Run output modal -->
<div class="modal fade" id="runModal" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header border-secondary">
        <h5 class="modal-title">
          <i class="bi bi-terminal me-2"></i>
          <span id="runModalTitle">Running…</span>
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body p-0">
        <pre id="runOutput" style="min-height:200px;max-height:55vh;margin:0;padding:1rem;background:#0d0d0d;color:#d0d0d0;font-size:.8rem;overflow:auto;border-radius:0;">
<span class="text-secondary">Waiting for output…</span></pre>
      </div>
      <div class="modal-footer border-secondary">
        <span id="runStatus" class="me-auto small text-secondary"></span>
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
      </div>
    </div>
  </div>
</div>

<!-- New Script modal -->
<div class="modal fade" id="newScriptModal" tabindex="-1">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header border-secondary">
        <h5 class="modal-title"><i class="bi bi-plus-circle me-2"></i>New Script</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <div class="mb-3">
          <label class="form-label">Directory</label>
          <select id="newScriptDir" class="form-select">
            <?php foreach ($allowed_dirs as $d): ?>
            <option value="<?= h($d) ?>"><?= h($d) ?>/</option>
            <?php endforeach; ?>
          </select>
        </div>
        <div class="mb-3">
          <label class="form-label">Filename</label>
          <div class="input-group">
            <input type="text" id="newScriptName" class="form-control" placeholder="my_collector">
            <span class="input-group-text">.py</span>
          </div>
          <div class="form-text">Use lowercase letters, numbers, and underscores.</div>
        </div>
      </div>
      <div class="modal-footer border-secondary">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-success" onclick="createNewScript()">
          <i class="bi bi-arrow-right-circle me-1"></i>Create & Edit
        </button>
      </div>
    </div>
  </div>
</div>

<?php
$extra_js = <<<'JS'
<script>
const runModal    = new bootstrap.Modal(document.getElementById('runModal'));
const newScriptMd = new bootstrap.Modal(document.getElementById('newScriptModal'));

function showNewScriptModal() { newScriptMd.show(); }

function createNewScript() {
  const dir  = document.getElementById('newScriptDir').value.trim();
  const name = document.getElementById('newScriptName').value.trim().replace(/\.py$/i,'').replace(/[^a-z0-9_]/gi,'_');
  if (!name) { alert('Please enter a filename.'); return; }
  const rel  = dir + '/' + name + '.py';
  // Create empty file then open editor
  apiPost(_api('api/scripts.php?action=save'), { path: rel, content: '#!/usr/bin/env python3\n# ' + name + '.py\n\n' })
    .then(() => { window.location.href = _api('script_edit.php?path=' + encodeURIComponent(rel)); })
    .catch(e => showToast(e.message, 'danger'));
}

function runScript(path, name) {
  document.getElementById('runModalTitle').textContent = name;
  document.getElementById('runOutput').innerHTML = '<span class="text-secondary">Running…</span>';
  document.getElementById('runStatus').textContent  = '';
  runModal.show();

  const start = Date.now();
  apiPost(_api('api/scripts.php?action=run'), { path })
    .then(r => {
      const elapsed = ((Date.now() - start) / 1000).toFixed(1);
      const pre = document.getElementById('runOutput');
      pre.textContent = r.output || '(no output)';
      const status = document.getElementById('runStatus');
      if (r.exit_code === 0) {
        status.innerHTML = '<span class="text-success"><i class="bi bi-check-circle me-1"></i>Exited 0 · ' + elapsed + 's</span>';
      } else {
        status.innerHTML = '<span class="text-danger"><i class="bi bi-x-circle me-1"></i>Exit code ' + r.exit_code + ' · ' + elapsed + 's</span>';
      }
    })
    .catch(e => {
      document.getElementById('runOutput').textContent = 'Error: ' + e.message;
      document.getElementById('runStatus').innerHTML = '<span class="text-danger">Failed</span>';
    });
}

function deleteScript(path, name) {
  confirmDialog(
    'Delete Script',
    `<p>Permanently delete <strong>${escHtml(name)}</strong>?</p><p class="text-warning small">This cannot be undone.</p>`,
    () => apiDelete(_api('api/scripts.php?path=' + encodeURIComponent(path)))
            .then(() => { showToast('Script deleted'); setTimeout(() => location.reload(), 600); })
            .catch(e => showToast(e.message, 'danger')),
    'btn-danger'
  );
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
