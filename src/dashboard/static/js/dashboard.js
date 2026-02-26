/**
 * Cannabis Data Aggregator — Shared Dashboard Utilities
 */

// ---------------------------------------------------------------------------
// Toast notifications
// ---------------------------------------------------------------------------
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const icons = {
    success: 'bi-check-circle-fill',
    danger:  'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info:    'bi-info-circle-fill',
  };
  const icon = icons[type] || icons.info;

  const id = 'toast_' + Date.now();
  const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert"
         style="min-width:280px;" data-bs-autohide="true" data-bs-delay="${duration}">
      <div class="d-flex">
        <div class="toast-body">
          <i class="bi ${icon} me-2"></i>${escHtml(message)}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast"></button>
      </div>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  const el = document.getElementById(id);
  const toast = new bootstrap.Toast(el);
  toast.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

// ---------------------------------------------------------------------------
// Loading overlay
// ---------------------------------------------------------------------------
function showLoading(show) {
  const el = document.getElementById('loadingOverlay');
  if (!el) return;
  el.style.display = show ? 'flex' : 'none';
}

// ---------------------------------------------------------------------------
// Confirm dialog (async, returns Promise<boolean>)
// ---------------------------------------------------------------------------
function confirmDialog(message, title = 'Confirm') {
  return new Promise(resolve => {
    // Re-use Bootstrap modal if available
    const existing = document.getElementById('confirmModal');
    if (existing) {
      document.getElementById('confirmModalTitle').textContent = title;
      document.getElementById('confirmModalBody').textContent = message;
      const modal = bootstrap.Modal.getOrCreateInstance(existing);
      const btn = document.getElementById('confirmModalOk');
      const newBtn = btn.cloneNode(true);
      btn.replaceWith(newBtn);
      newBtn.addEventListener('click', () => { modal.hide(); resolve(true); });
      existing.addEventListener('hidden.bs.modal', () => resolve(false), { once: true });
      modal.show();
    } else {
      resolve(window.confirm(message));
    }
  });
}

// ---------------------------------------------------------------------------
// HTML escape helper
// ---------------------------------------------------------------------------
function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// ---------------------------------------------------------------------------
// Format helpers
// ---------------------------------------------------------------------------
function fmtNumber(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString();
}

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

function fmtDateRelative(iso) {
  if (!iso) return '—';
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins  = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days  = Math.floor(diff / 86400000);
    if (mins < 1)   return 'just now';
    if (mins < 60)  return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  } catch { return iso; }
}

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------
function statusBadge(status) {
  const map = {
    success: ['badge-success', 'Success'],
    failed:  ['badge-failed',  'Failed'],
    running: ['badge-running', 'Running'],
    partial: ['badge-partial', 'Partial'],
    skipped: ['badge-skipped', 'Skipped'],
  };
  const [cls, label] = map[status] || ['bg-secondary', status || 'Unknown'];
  return `<span class="badge ${cls}">${escHtml(label)}</span>`;
}

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------
async function apiGet(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function apiPost(url, data) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return { ok: resp.ok, status: resp.status, data: await resp.json() };
}

async function apiPut(url, data) {
  const resp = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return { ok: resp.ok, status: resp.status, data: await resp.json() };
}

async function apiDelete(url) {
  const resp = await fetch(url, { method: 'DELETE' });
  return { ok: resp.ok, status: resp.status, data: await resp.json().catch(() => ({})) };
}

// ---------------------------------------------------------------------------
// Download trigger
// ---------------------------------------------------------------------------
function triggerDownload(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || '';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// ---------------------------------------------------------------------------
// URL query param helpers
// ---------------------------------------------------------------------------
function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function buildQueryString(params) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && v !== '') q.set(k, v);
  }
  const s = q.toString();
  return s ? '?' + s : '';
}

// ---------------------------------------------------------------------------
// Debounce
// ---------------------------------------------------------------------------
function debounce(fn, ms = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

// ---------------------------------------------------------------------------
// Source actions (shared across dashboard and sources pages)
// ---------------------------------------------------------------------------
async function runSource(sourceId, name) {
  if (!await confirmDialog(`Run collection for "${name}" now?`, 'Run Now')) return;
  showLoading(true);
  try {
    const r = await apiPost(`/api/sources/${sourceId}/run`, {});
    showLoading(false);
    if (r.ok) {
      showToast(`Collection started for ${name}`, 'success');
    } else {
      showToast(r.data.error || 'Failed to trigger collection', 'danger');
    }
  } catch (err) {
    showLoading(false);
    showToast('Request failed: ' + err.message, 'danger');
  }
}

async function toggleSource(sourceId, enabled, rowEl) {
  try {
    const r = await apiPost(`/api/sources/${sourceId}/toggle`, {});
    if (!r.ok) {
      showToast(r.data.error || 'Toggle failed', 'danger');
      // Revert the checkbox
      if (rowEl) {
        const cb = rowEl.querySelector('input[type=checkbox]');
        if (cb) cb.checked = !cb.checked;
      }
    }
  } catch (err) {
    showToast('Request failed: ' + err.message, 'danger');
  }
}

async function deleteSource(sourceId, name) {
  if (!await confirmDialog(`Delete source "${name}"? This cannot be undone.`, 'Delete Source')) return;
  showLoading(true);
  try {
    const r = await apiDelete(`/api/sources/${sourceId}`);
    showLoading(false);
    if (r.ok) {
      showToast(`Source "${name}" deleted.`, 'success');
      setTimeout(() => location.reload(), 900);
    } else {
      showToast(r.data.error || 'Delete failed', 'danger');
    }
  } catch (err) {
    showLoading(false);
    showToast('Request failed: ' + err.message, 'danger');
  }
}

// ---------------------------------------------------------------------------
// Schedule actions
// ---------------------------------------------------------------------------
async function deleteSchedule(schedId, name) {
  if (!await confirmDialog(`Delete schedule "${name}"?`, 'Delete Schedule')) return;
  showLoading(true);
  try {
    const r = await apiDelete(`/api/schedules/${schedId}`);
    showLoading(false);
    if (r.ok) {
      showToast(`Schedule "${name}" deleted.`, 'success');
      setTimeout(() => location.reload(), 900);
    } else {
      showToast(r.data.error || 'Delete failed', 'danger');
    }
  } catch (err) {
    showLoading(false);
    showToast('Request failed: ' + err.message, 'danger');
  }
}

async function toggleSchedule(schedId, rowEl) {
  try {
    const r = await apiPost(`/api/schedules/${schedId}/toggle`, {});
    if (!r.ok) {
      showToast(r.data.error || 'Toggle failed', 'danger');
      if (rowEl) {
        const cb = rowEl.querySelector('input[type=checkbox]');
        if (cb) cb.checked = !cb.checked;
      }
    }
  } catch (err) {
    showToast('Request failed: ' + err.message, 'danger');
  }
}

// ---------------------------------------------------------------------------
// Confirm modal injection (if not already in base.html)
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('confirmModal')) return; // already present
  document.body.insertAdjacentHTML('beforeend', `
    <div class="modal fade" id="confirmModal" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered modal-sm">
        <div class="modal-content">
          <div class="modal-header">
            <h6 class="modal-title" id="confirmModalTitle">Confirm</h6>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" id="confirmModalBody"></div>
          <div class="modal-footer">
            <button type="button" class="btn btn-sm btn-outline-secondary"
                    data-bs-dismiss="modal">Cancel</button>
            <button type="button" class="btn btn-sm btn-danger"
                    id="confirmModalOk">Confirm</button>
          </div>
        </div>
      </div>
    </div>`);
});
