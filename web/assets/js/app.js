/* ─────────────────────────────────────────────────────────────────────────────
   Cannabis Data Aggregator – Shared JS
   ───────────────────────────────────────────────────────────────────────────── */

'use strict';

// ── Sidebar toggle ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('sidebarToggle');
  if (btn) {
    btn.addEventListener('click', () => {
      document.body.classList.toggle('sidebar-collapsed');
      localStorage.setItem('sidebarCollapsed', document.body.classList.contains('sidebar-collapsed'));
    });
  }
  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    document.body.classList.add('sidebar-collapsed');
  }
});

// ── Toast ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = 'success', delay = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const colors = { success:'text-bg-success', danger:'text-bg-danger', warning:'text-bg-warning', info:'text-bg-info' };
  const id = 'toast_' + Date.now();
  container.insertAdjacentHTML('beforeend', `
    <div id="${id}" class="toast align-items-center ${colors[type] ?? 'text-bg-secondary'} border-0" role="alert">
      <div class="d-flex">
        <div class="toast-body">${escHtml(msg)}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`);
  const el = document.getElementById(id);
  const t  = new bootstrap.Toast(el, { delay });
  t.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ── Confirm dialog ────────────────────────────────────────────────────────────
function confirmDialog(title, body, onConfirm, btnClass = 'btn-danger') {
  const modal  = document.getElementById('confirmModal');
  const bsModal = bootstrap.Modal.getOrCreateInstance(modal);
  document.getElementById('confirmModalTitle').textContent = title;
  document.getElementById('confirmModalBody').innerHTML = body;
  const okBtn = document.getElementById('confirmModalOk');
  okBtn.className = 'btn ' + btnClass;
  const handler = () => { bsModal.hide(); onConfirm(); okBtn.removeEventListener('click', handler); };
  okBtn.addEventListener('click', handler);
  bsModal.show();
}

// ── Escape HTML ───────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── Format helpers ─────────────────────────────────────────────────────────────
function fmtNumber(n) { return n != null ? Number(n).toLocaleString() : '–'; }
function fmtDate(d, full = false) {
  if (!d) return '–';
  const dt = new Date(d);
  if (isNaN(dt)) return d;
  return full ? dt.toLocaleString() : dt.toLocaleDateString();
}
function fmtAgo(d) {
  if (!d) return '–';
  const diff = (Date.now() - new Date(d)) / 1000;
  if (diff < 60)    return Math.round(diff) + 's ago';
  if (diff < 3600)  return Math.round(diff/60)   + 'm ago';
  if (diff < 86400) return Math.round(diff/3600)  + 'h ago';
  return Math.round(diff/86400) + 'd ago';
}
function fmtDuration(s) {
  if (s == null) return '–';
  if (s < 60)   return s.toFixed(1) + 's';
  if (s < 3600) return (s/60).toFixed(1)   + 'm';
  return (s/3600).toFixed(1) + 'h';
}
function statusBadge(s) {
  const m = { success:'bg-success', failed:'bg-danger', running:'bg-primary', partial:'bg-warning text-dark', skipped:'bg-secondary' };
  return `<span class="badge ${m[s]??'bg-secondary'}">${escHtml(s)}</span>`;
}

// ── API helpers ───────────────────────────────────────────────────────────────
async function apiGet(url) {
  const r = await fetch(url, { headers: { Accept: 'application/json' } });
  if (!r.ok) throw new Error((await r.json().catch(() => ({error: r.statusText}))).error);
  return r.json();
}

async function apiPost(url, data = {}) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error((await r.json().catch(() => ({error: r.statusText}))).error);
  return r.json();
}

async function apiDelete(url) {
  const r = await fetch(url, { method: 'DELETE', headers: { Accept: 'application/json' } });
  if (!r.ok) throw new Error((await r.json().catch(() => ({error: r.statusText}))).error);
  return r.json();
}

// ── API base (WEB_BASE is injected by footer.php as a <script> tag) ───────────
const _api = (path) => (typeof WEB_BASE !== 'undefined' ? WEB_BASE : '/') + path;

// ── Source actions ────────────────────────────────────────────────────────────
function toggleSource(sourceId, enable) {
  const action = enable ? 'enable' : 'disable';
  apiPost(_api(`api/sources.php?action=${action}&id=${encodeURIComponent(sourceId)}`))
    .then(() => { showToast(`Source ${action}d`); setTimeout(() => location.reload(), 800); })
    .catch(e => showToast(e.message, 'danger'));
}

function deleteSource(sourceId, name) {
  confirmDialog(
    'Delete Source',
    `<p>Delete <strong>${escHtml(name)}</strong>?</p><p class="text-warning small">This will also delete all associated records and logs.</p>`,
    () => apiDelete(_api(`api/sources.php?id=${encodeURIComponent(sourceId)}`))
            .then(() => { showToast('Source deleted'); setTimeout(() => location.reload(), 800); })
            .catch(e => showToast(e.message, 'danger'))
  );
}

function runSource(sourceId, name) {
  showToast(`Queuing collection for ${name}…`, 'info');
  apiPost(_api(`api/sources.php?action=run&id=${encodeURIComponent(sourceId)}`))
    .then(r => showToast(r.message ?? 'Collection started', 'success'))
    .catch(e => showToast(e.message, 'danger'));
}

// ── Schedule actions ──────────────────────────────────────────────────────────
function deleteSchedule(schedId, name) {
  confirmDialog(
    'Delete Schedule',
    `Delete schedule <strong>${escHtml(name)}</strong>?`,
    () => apiDelete(_api(`api/schedules.php?id=${encodeURIComponent(schedId)}`))
            .then(() => { showToast('Schedule deleted'); setTimeout(() => location.reload(), 800); })
            .catch(e => showToast(e.message, 'danger'))
  );
}

function toggleSchedule(schedId, enable) {
  apiPost(_api(`api/schedules.php?action=${enable ? 'enable' : 'disable'}&id=${encodeURIComponent(schedId)}`))
    .then(() => { showToast('Schedule updated'); setTimeout(() => location.reload(), 800); })
    .catch(e => showToast(e.message, 'danger'));
}

// ── Loading overlay ───────────────────────────────────────────────────────────
function showLoading(show = true, selector = '#loadingOverlay') {
  const el = document.querySelector(selector);
  if (el) el.style.display = show ? 'flex' : 'none';
}

// ── Download helper ───────────────────────────────────────────────────────────
function triggerDownload(url, filename) {
  const a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ── Debounce ──────────────────────────────────────────────────────────────────
function debounce(fn, ms = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}
