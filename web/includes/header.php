<?php
/**
 * header.php – Shared HTML header + sidebar navigation.
 * Include at top of every page AFTER setting $page_title.
 */

require_once __DIR__ . '/functions.php';

if (session_status() === PHP_SESSION_NONE) session_start();

$page_title   = $page_title ?? APP_NAME;
$active_page  = $active_page ?? '';

// Use the absolute URL base computed in config.php — works at any nesting depth.
$base = WEB_BASE;
?>
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title><?= h($page_title) ?> – <?= h(APP_NAME) ?></title>
  <!-- Bootstrap 5 -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
  <!-- Font Awesome -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.2/css/all.min.css">
  <!-- Bootstrap Icons -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
  <!-- Custom theme -->
  <link rel="stylesheet" href="<?= $base ?>assets/css/custom.css">
</head>
<body>

<!-- ── Sidebar ──────────────────────────────────────────────────────────── -->
<div class="d-flex" id="wrapper">

<nav id="sidebar" class="d-flex flex-column flex-shrink-0 p-3">

  <!-- Brand -->
  <a href="<?= $base ?>index.php" class="d-flex align-items-center gap-2 mb-2 text-decoration-none" style="padding:.4rem .5rem">
    <div style="width:30px;height:30px;background:linear-gradient(135deg,#2ea043,#20c997);border-radius:6px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 12px rgba(46,160,67,.35);flex-shrink:0">
      <i class="fas fa-seedling" style="color:#fff;font-size:.85rem;margin:0"></i>
    </div>
    <span class="fs-6 fw-bold" style="color:#e6edf3;font-size:.82rem!important;letter-spacing:-.01em;white-space:nowrap"><?= h(APP_NAME) ?></span>
  </a>

  <hr class="border-secondary">

  <ul class="nav nav-pills flex-column gap-1" style="flex:1">

    <!-- Collection -->
    <li class="mt-1 mb-1 px-2">
      <small class="text-uppercase text-secondary fw-semibold" style="font-size:.62rem;letter-spacing:.1em">Collection</small>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>index.php" class="nav-link <?= $active_page === 'dashboard' ? 'active' : '' ?>">
        <i class="fas fa-gauge-high"></i> Dashboard
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>sources.php" class="nav-link <?= $active_page === 'sources' ? 'active' : '' ?>">
        <i class="fas fa-database"></i> Data Sources
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>schedules.php" class="nav-link <?= $active_page === 'schedules' ? 'active' : '' ?>">
        <i class="fas fa-clock"></i> Schedules
      </a>
    </li>

    <!-- Data -->
    <li class="mt-2 mb-1 px-2">
      <small class="text-uppercase text-secondary fw-semibold" style="font-size:.62rem;letter-spacing:.1em">Data</small>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>data.php" class="nav-link <?= $active_page === 'data' ? 'active' : '' ?>">
        <i class="fas fa-table"></i> Browse Records
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>map.php" class="nav-link <?= $active_page === 'map' ? 'active' : '' ?>">
        <i class="fas fa-map-location-dot"></i> Map View
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>exports.php" class="nav-link <?= $active_page === 'exports' ? 'active' : '' ?>">
        <i class="fas fa-file-arrow-down"></i> Export
      </a>
    </li>

    <!-- System -->
    <li class="mt-2 mb-1 px-2">
      <small class="text-uppercase text-secondary fw-semibold" style="font-size:.62rem;letter-spacing:.1em">System</small>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>logs.php" class="nav-link <?= $active_page === 'logs' ? 'active' : '' ?>">
        <i class="fas fa-scroll"></i> Logs
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>scripts.php" class="nav-link <?= $active_page === 'scripts' ? 'active' : '' ?>">
        <i class="fas fa-terminal"></i> Scripts
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>settings.php" class="nav-link <?= $active_page === 'settings' ? 'active' : '' ?>">
        <i class="fas fa-gear"></i> Settings
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>instructions.php" class="nav-link <?= $active_page === 'instructions' ? 'active' : '' ?>">
        <i class="fas fa-book-open"></i> Instructions
      </a>
    </li>

  </ul>

  <hr class="border-secondary" style="margin-top:.75rem">
  <div style="font-size:.7rem;color:#484f58;padding-left:.25rem">
    v<?= h(APP_VERSION) ?> &nbsp;·&nbsp; <?= date('m/d/Y') ?>
  </div>

</nav>

<!-- ── Main content ──────────────────────────────────────────────────────── -->
<div id="page-content" class="flex-grow-1 overflow-auto">

  <!-- Top bar -->
  <div class="topbar">
    <button class="btn btn-sm btn-outline-secondary" id="sidebarToggle" title="Toggle sidebar">
      <i class="fas fa-bars"></i>
    </button>
    <h6 class="mb-0 fw-semibold"><?= h($page_title) ?></h6>
    <div class="ms-auto d-flex align-items-center gap-2">
      <span id="db-status" class="badge bg-success" title="Database connected">
        <i class="fas fa-circle-dot me-1"></i>Live
      </span>
    </div>
  </div>

  <!-- Flash messages -->
  <?php if (!empty($_SESSION['flash'])): ?>
  <div class="px-4 pt-3">
    <?php foreach ($_SESSION['flash'] as $fl): ?>
    <div class="alert alert-<?= h($fl['type']) ?> alert-dismissible fade show" role="alert">
      <?= h($fl['msg']) ?>
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    <?php endforeach; ?>
  </div>
  <?php $_SESSION['flash'] = []; endif; ?>

  <!-- Actual page body starts here -->
  <div class="px-4 py-3">
