  </div><!-- /px-4 py-3 -->
</div><!-- /page-content -->
</div><!-- /wrapper -->

<!-- Toast container -->
<div class="toast-container position-fixed bottom-0 end-0 p-3" id="toastContainer"></div>

<!-- Confirm modal -->
<div class="modal fade" id="confirmModal" tabindex="-1">
  <div class="modal-dialog modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header border-secondary">
        <h5 class="modal-title" id="confirmModalTitle">
            <i class="bi bi-exclamation-triangle-fill text-warning"></i>
            Confirm
        </h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="confirmModalBody"></div>
      <div class="modal-footer border-secondary">
        <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">
            <i class="fas fa-times"></i>
            Cancel
        </button>
        <button type="button" class="btn btn-danger btn-sm" id="confirmModalOk">
            <i class="fas fa-check"></i>
            Confirm
        </button>
      </div>
    </div>
  </div>
</div>

<!-- Bootstrap JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@latest/dist/js/bootstrap.bundle.min.js"></script>
  <!-- jQuery -->
<script src="https://cdn.jsdelivr.net/npm/jquery@latest/dist/jquery.min.js"></script>
<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@latest/dist/chart.umd.min.js"></script>
<!-- Expose server-computed base path to JavaScript -->
<script>const WEB_BASE = <?= json_encode(WEB_BASE) ?>;</script>
<!-- Shared app JS -->
<script src="<?= WEB_BASE ?>assets/js/app.js"></script>

<?php if (!empty($extra_js)) echo $extra_js; ?>
</body>
</html>
