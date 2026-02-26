<?php
$page_title  = 'Instructions & Docs';
$active_page = 'instructions';
require_once __DIR__ . '/includes/header.php';

// Resolve docs directory
$docs_dir = dirname(__DIR__) . '/docs';

// Available docs – label => filename
$docs = [
    'instructions'   => ['label' => 'Web UI Guide',          'file' => 'INSTRUCTIONS.md'],
    'data_acq'       => ['label' => 'Data Acquisition Guide', 'file' => 'DATA_ACQUISITION.md'],
];

$active_doc = $_GET['doc'] ?? 'instructions';
if (!array_key_exists($active_doc, $docs)) $active_doc = 'instructions';

$doc_file = $docs_dir . '/' . $docs[$active_doc]['file'];
$content  = file_exists($doc_file) ? htmlspecialchars(file_get_contents($doc_file), ENT_QUOTES, 'UTF-8') : '';
?>

<div class="row g-3">
  <!-- Tab selector -->
  <div class="col-12">
    <ul class="nav nav-tabs border-secondary" id="docTabs">
      <?php foreach ($docs as $key => $d): ?>
      <li class="nav-item">
        <a class="nav-link <?= $active_doc === $key ? 'active' : 'text-secondary' ?>" href="?doc=<?= urlencode($key) ?>">
            <i class="fas fa-book-open me-1"></i>
          <?= htmlspecialchars($d['label']) ?>
        </a>
      </li>
      <?php endforeach; ?>
    </ul>
  </div>

  <!-- Document content -->
  <div class="col-12">
    <div class="card">
      <div class="card-header border-secondary d-flex justify-content-between align-items-center">
        <span>
            <?= htmlspecialchars($docs[$active_doc]['label']) ?>
        </span>
        <a href="?doc=<?= urlencode($active_doc) ?>&raw=1" class="btn btn-sm btn-outline-secondary" target="_blank">
          <i class="fas fa-file-alt me-1"></i>
            View Raw
        </a>
      </div>
      <div class="card-body">
        <!-- markdown rendered here -->
        <div id="doc-output" class="doc-body">
          <div class="text-center py-5 text-secondary">
            <i class="fas fa-spinner spin fa-2x"></i>
            <p class="mt-2">Loading…</p>
          </div>
        </div>
        <!-- raw markdown hidden in a pre for marked.js to parse -->
        <pre id="doc-raw" class="d-none">
            <?= $content ?>
        </pre>
      </div>
    </div>
  </div>
</div>

<?php
// Raw output mode – serve plain text
if (!empty($_GET['raw']) && file_exists($doc_file)) {
    // Already output headers? No – header.php hasn't flushed yet at this point
    // but we need to catch it. Use output buffering trick.
    ob_end_clean();
    header('Content-Type: text/plain; charset=utf-8');
    readfile($doc_file);
    exit;
}
?>

<?php
$extra_js = <<<'JS'
<!-- marked.js for Markdown rendering -->
<script src="https://cdn.jsdelivr.net/npm/marked@latest/marked.min.js"></script>
<!-- Jquery for DOM manipulation (optional, but can simplify some tasks) -->
<script src="https://cdn.jsdelivr.net/npm/jquery@latest/dist/jquery.min.js"></script>
<!-- highlight.js for code blocks -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@latest/styles/github-dark.min.css">
<script src="https://cdn.jsdelivr.net/npm/highlight.js@latest/highlight.min.js"></script>
<style>
.doc-body { font-size: .9375rem; line-height: 1.7; }
.doc-body h1 { font-size: 1.6rem; border-bottom: 1px solid #333; padding-bottom: .4rem; margin-top: 1.5rem; }
.doc-body h2 { font-size: 1.25rem; border-bottom: 1px solid #222; padding-bottom: .3rem; margin-top: 1.4rem; }
.doc-body h3 { font-size: 1.05rem; margin-top: 1.2rem; }
.doc-body table { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: .875rem; }
.doc-body th, .doc-body td { border: 1px solid #333; padding: .45rem .75rem; text-align: left; }
.doc-body th { background: #1a1a1a; color: #ccc; }
.doc-body tr:hover td { background: rgba(255,255,255,.03); }
.doc-body code:not(.hljs) { background: #1e1e1e; color: #d0d0d0; padding: .15em .35em; border-radius: .25rem; font-size: .87em; }
.doc-body pre { background: #0d0d0d; border-radius: .375rem; padding: 1rem; overflow: auto; margin: 1rem 0; }
.doc-body pre code { background: none; padding: 0; }
.doc-body blockquote { border-left: 3px solid #198754; padding: .5rem 1rem; background: rgba(25,135,84,.08); border-radius: 0 .375rem .375rem 0; margin: 1rem 0; color: #ccc; }
.doc-body a { color: #4db88c; }
.doc-body a:hover { color: #6fd4a8; }
.doc-body hr { border-color: #333; margin: 1.5rem 0; }
.doc-body ul, .doc-body ol { padding-left: 1.5rem; }
.doc-body li { margin-bottom: .25rem; }
/* checkboxes in GFM task lists */
.doc-body li input[type=checkbox] { margin-right: .4rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { display: inline-block; animation: spin 1s linear infinite; }
</style>
<script>
(function () {
  const raw = document.getElementById('doc-raw');
  const out = document.getElementById('doc-output');
  if (!raw || !out) return;

  // Configure marked
  marked.setOptions({
    gfm:    true,
    breaks: false,
    pedantic: false,
  });

  // Custom renderer for highlight.js
  const renderer = new marked.Renderer();
  renderer.code = function (code, lang) {
    const validLang = lang && hljs.getLanguage(lang) ? lang : 'plaintext';
    const highlighted = hljs.highlight(code, { language: validLang, ignoreIllegals: true }).value;
    return `<pre><code class="hljs language-${validLang}">${highlighted}</code></pre>`;
  };

  const md = raw.textContent;
  out.innerHTML = marked.parse(md, { renderer });

  // Process GFM task-list items ([ ] and [x])
  out.querySelectorAll('li').forEach(li => {
    const t = li.childNodes[0];
    if (t && t.nodeType === Node.TEXT_NODE) {
      if (t.textContent.startsWith('[ ] ')) {
        const cb = document.createElement('input');
        cb.type = 'checkbox'; cb.disabled = true;
        li.insertBefore(cb, t);
        t.textContent = t.textContent.slice(4);
      } else if (t.textContent.startsWith('[x] ')) {
        const cb = document.createElement('input');
        cb.type = 'checkbox'; cb.disabled = true; cb.checked = true;
        li.insertBefore(cb, t);
        t.textContent = t.textContent.slice(4);
      }
    }
  });
})();
</script>
JS;
require_once __DIR__ . '/includes/footer.php';
?>
