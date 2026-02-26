<?php
$page_title  = 'Script Editor';
$active_page = 'scripts';
require_once __DIR__ . '/includes/header.php';

// Allowed directories
$allowed_dirs = ['scripts', 'src', 'src/collectors', 'src/storage', 'src/utils'];

// Resolve the path being edited (may be empty for a new file passed via ?path)
$rel_path = trim($_GET['path'] ?? '');

// Validate: must have .py extension and start with an allowed dir
$valid_path = false;
$dir_part   = '';
$file_part  = '';
if ($rel_path !== '') {
    $rel_path   = str_replace('\\', '/', $rel_path);            // normalise
    $parts      = explode('/', $rel_path, 2);
    $dir_part   = count($parts) >= 2 ? implode('/', array_slice($parts, 0, count($parts) - 1)) : '';
    $file_part  = basename($rel_path);

    // Confirm top-level dir or subdir prefix is in the allowed list
    foreach ($allowed_dirs as $ad) {
        if ($rel_path === $ad . '/' . $file_part || strpos($rel_path, $ad . '/') === 0) {
            $valid_path = true;
            break;
        }
    }
    if (!preg_match('/\.py$/i', $file_part)) $valid_path = false;
}

// Read existing content
$initial_content = '';
if ($valid_path) {
    $abs = APP_ROOT . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $rel_path);
    if (file_exists($abs)) {
        $initial_content = file_get_contents($abs);
    }
}

$is_new = ($initial_content === '' && !file_exists($abs ?? ''));
$page_title = $valid_path
    ? ($is_new ? 'New Script' : 'Edit: ' . $file_part)
    : 'Script Editor';
?>

<div class="d-flex justify-content-between align-items-center mb-3">
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb mb-0">
      <li class="breadcrumb-item">
        <a href="<?= WEB_BASE ?>scripts.php" class="text-success">Scripts</a>
      </li>
      <?php if ($valid_path): ?>
      <li class="breadcrumb-item text-secondary"><?= h($dir_part) ?></li>
      <li class="breadcrumb-item active"><?= h($file_part) ?></li>
      <?php else: ?>
      <li class="breadcrumb-item active">Editor</li>
      <?php endif; ?>
    </ol>
  </nav>
  <div class="d-flex gap-2">
    <button id="btnSave" class="btn btn-success btn-sm" onclick="saveScript()">
      <i class="bi bi-floppy me-1"></i>Save
    </button>
    <?php if ($valid_path): ?>
    <button id="btnRun" class="btn btn-primary btn-sm" onclick="runScript()">
      <i class="bi bi-play-fill me-1"></i>Run
    </button>
    <?php endif; ?>
    <a href="<?= WEB_BASE ?>scripts.php" class="btn btn-outline-secondary btn-sm">
      <i class="bi bi-x-lg me-1"></i>Close
    </a>
  </div>
</div>

<?php if (!$valid_path): ?>
<div class="alert alert-warning">
  <i class="bi bi-exclamation-triangle me-2"></i>
  <strong>Invalid or missing script path.</strong>
  The <code>path</code> parameter must point to a <code>.py</code> file inside one of the allowed directories:
  <code><?= h(implode(', ', $allowed_dirs)) ?></code>.
  <a href="<?= WEB_BASE ?>scripts.php" class="alert-link ms-2">← Back to Scripts</a>
</div>
<?php else: ?>

<!-- File path display -->
<div class="card mb-2">
  <div class="card-body py-2 px-3 d-flex align-items-center gap-3">
    <i class="bi bi-filetype-py text-primary fs-5"></i>
    <code id="scriptPath" class="text-info"><?= h($rel_path) ?></code>
    <span id="saveBadge" class="badge bg-secondary ms-auto d-none">Unsaved changes</span>
  </div>
</div>

<!-- CodeMirror editor -->
<div class="card mb-3">
  <div class="card-header border-secondary d-flex align-items-center justify-content-between py-2">
    <span class="small text-secondary">
      <i class="bi bi-code-slash me-1"></i>Python
    </span>
    <div class="d-flex align-items-center gap-3">
      <div class="form-check form-switch mb-0">
        <input class="form-check-input" type="checkbox" id="wordWrapToggle" onchange="toggleWordWrap(this.checked)">
        <label class="form-check-label small text-secondary" for="wordWrapToggle">Word wrap</label>
      </div>
      <span id="lineCol" class="small text-secondary">Ln 1, Col 1</span>
    </div>
  </div>
  <div class="card-body p-0">
    <!-- CodeMirror will replace this textarea -->
    <textarea id="codeEditor"><?= htmlspecialchars($initial_content, ENT_QUOTES, 'UTF-8') ?></textarea>
  </div>
</div>

<!-- Output console -->
<div class="card" id="outputCard" style="display:none">
  <div class="card-header border-secondary d-flex align-items-center justify-content-between py-2">
    <span><i class="bi bi-terminal me-2"></i>Output</span>
    <div class="d-flex align-items-center gap-2">
      <span id="runStatus" class="small"></span>
      <button class="btn btn-sm btn-outline-secondary" onclick="clearOutput()">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  </div>
  <div class="card-body p-0">
    <pre id="runOutput" style="margin:0;padding:1rem;background:#0d0d0d;color:#d0d0d0;font-size:.8rem;min-height:120px;max-height:40vh;overflow:auto;border-radius:0 0 .375rem .375rem;"></pre>
  </div>
</div>

<!-- Hidden data -->
<input type="hidden" id="currentRelPath" value="<?= h($rel_path) ?>">

<?php endif; ?>

<?php
$extra_js = <<<'JS'
<!-- CodeMirror 5 -->
<link  rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5/lib/codemirror.css">
<link  rel="stylesheet" href="https://cdn.jsdelivr.net/npm/codemirror@5/theme/dracula.css">
<script src="https://cdn.jsdelivr.net/npm/codemirror@5/lib/codemirror.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5/mode/python/python.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/edit/closebrackets.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/edit/matchbrackets.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/selection/active-line.js"></script>
<script src="https://cdn.jsdelivr.net/npm/codemirror@5/addon/comment/comment.js"></script>
<style>
.CodeMirror {
  height: 60vh;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  font-size: .875rem;
  line-height: 1.6;
  border-radius: 0 0 .375rem .375rem;
}
.CodeMirror-scroll { padding-bottom: 2rem; }
</style>
<script>
const ta = document.getElementById('codeEditor');
if (ta) {
  var editor = CodeMirror.fromTextArea(ta, {
    mode:             'python',
    theme:            'dracula',
    lineNumbers:      true,
    autoCloseBrackets: true,
    matchBrackets:    true,
    styleActiveLine:  true,
    indentUnit:       4,
    tabSize:          4,
    indentWithTabs:   false,
    extraKeys: {
      'Tab':       cm => cm.execCommand('indentMore'),
      'Shift-Tab': cm => cm.execCommand('indentLess'),
      'Ctrl-/'  :  cm => cm.toggleComment(),
      'Cmd-/'   :  cm => cm.toggleComment(),
      'Ctrl-S'  :  ()  => saveScript(),
      'Cmd-S'   :  ()  => saveScript(),
    },
  });

  // Track unsaved changes
  let dirty = false;
  editor.on('change', () => {
    if (!dirty) {
      dirty = true;
      document.getElementById('saveBadge').classList.remove('d-none');
    }
  });

  // Line / col indicator
  editor.on('cursorActivity', () => {
    const cur = editor.getCursor();
    document.getElementById('lineCol').textContent = `Ln ${cur.line + 1}, Col ${cur.ch + 1}`;
  });

  function toggleWordWrap(on) {
    editor.setOption('lineWrapping', on);
  }

  function saveScript() {
    const path    = document.getElementById('currentRelPath').value;
    const content = editor.getValue();
    document.getElementById('btnSave').disabled = true;
    apiPost(_api('api/scripts.php?action=save'), { path, content })
      .then(r => {
        showToast(r.message ?? 'Saved', 'success');
        dirty = false;
        document.getElementById('saveBadge').classList.add('d-none');
      })
      .catch(e => showToast('Save failed: ' + e.message, 'danger'))
      .finally(() => { document.getElementById('btnSave').disabled = false; });
  }

  function runScript() {
    const path = document.getElementById('currentRelPath').value;
    // Auto-save first
    const content = editor.getValue();
    apiPost(_api('api/scripts.php?action=save'), { path, content })
      .then(() => {
        dirty = false;
        document.getElementById('saveBadge').classList.add('d-none');
        startRun(path);
      })
      .catch(e => showToast('Save failed before run: ' + e.message, 'danger'));
  }

  function startRun(path) {
    const card   = document.getElementById('outputCard');
    const output = document.getElementById('runOutput');
    const status = document.getElementById('runStatus');
    const btnRun = document.getElementById('btnRun');

    card.style.display = '';
    output.textContent = 'Running…\n';
    status.innerHTML   = '<span class="text-secondary"><i class="bi bi-arrow-clockwise spin me-1"></i>Running</span>';
    btnRun.disabled    = true;
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });

    const start = Date.now();
    apiPost(_api('api/scripts.php?action=run'), { path })
      .then(r => {
        const elapsed = ((Date.now() - start) / 1000).toFixed(1);
        output.textContent = r.output || '(no output)';
        if (r.exit_code === 0) {
          status.innerHTML = `<span class="text-success"><i class="bi bi-check-circle me-1"></i>Exit 0 · ${elapsed}s</span>`;
        } else {
          status.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle me-1"></i>Exit ${r.exit_code} · ${elapsed}s</span>`;
        }
      })
      .catch(e => {
        output.textContent = 'Error: ' + e.message;
        status.innerHTML   = '<span class="text-danger">Failed</span>';
      })
      .finally(() => { btnRun.disabled = false; });
  }

  function clearOutput() {
    document.getElementById('runOutput').textContent = '';
    document.getElementById('runStatus').innerHTML   = '';
  }

  // Warn on unload if dirty
  window.addEventListener('beforeunload', e => {
    if (dirty) { e.preventDefault(); e.returnValue = ''; }
  });

  // Expose for inline onclick handlers
  window.saveScript  = saveScript;
  window.runScript   = runScript;
  window.clearOutput = clearOutput;
  window.toggleWordWrap = toggleWordWrap;
}
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
