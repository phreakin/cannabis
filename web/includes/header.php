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
// e.g. /cannabis-data-aggregator/web/   so links never break.
$base = WEB_BASE;
?>
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <link rel="stylesheet" type="text/css" href="../assets/css/custom.css"/>
    <link rel="stylesheet" type="text/css" href="../assets/css/custom.css"/>
    <link rel="stylesheet" type="text/css" href="../assets/css/custom.css"/>
    <link rel="stylesheet" type="text/css" href="../assets/css/custom.css"/>
    <link rel="stylesheet" type="text/css" href="../assets/css/custom.css"/>
    <meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= h($page_title) ?> – <?= h(APP_NAME) ?></title>

<!-- Bootstrap 5 -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@latest/dist/css/bootstrap.min.css">
<!-- Font Awesome -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@latest/css/all.min.css">
<!-- Bootstrap Icons -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@latest/font/bootstrap-icons.min.css">
<!-- Chart.js (loaded in footer) -->
<!-- Leaflet (loaded per-page) -->
<!-- Custom -->
<link rel="stylesheet" href="<?= $base ?>assets/css/custom.css">
</head>
<body>

<!-- ── Sidebar ──────────────────────────────────────────────────────────── -->
<div class="d-flex" id="wrapper">

<nav id="sidebar" class="d-flex flex-column flex-shrink-0 p-3">
  <a href="<?= $base ?>index.php" class="d-flex align-items-center mb-3 text-decoration-none link-light">
    <i class="fas fa-seedling me-2"></i>
    <span class="fs-6 fw-semibold">
        <?= h(APP_NAME) ?>
    </span>
  </a>
  <hr class="border-secondary">

  <ul class="nav nav-pills flex-column mb-auto gap-1">
    <li class="nav-item">
      <a href="<?= $base ?>index.php"
         class="nav-link <?= $active_page === 'dashboard' ? 'active' : 'link-light' ?>">
        <i class="fas fa-tachometer-alt me-2"></i>
          Dashboard
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>sources.php"
         class="nav-link <?= $active_page === 'sources' ? 'active' : 'link-light' ?>">
        <i class="fas fa-database me-2"></i>
          Data Sources
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>schedules.php"
         class="nav-link <?= $active_page === 'schedules' ? 'active' : 'link-light' ?>">
        <i class="fas fa-clock me-2"></i>
          Schedules
      </a>
    </li>

    <li class="mt-2 mb-1 px-2">
      <small class="text-uppercase text-secondary fw-semibold">
          <i class="fas fa-database me-2"></i>
          Data
      </small>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>data.php"
         class="nav-link <?= $active_page === 'data' ? 'active' : 'link-light' ?>">
        <i class="fas fa-table me-2"></i>
          Browse Records
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>map.php"
         class="nav-link <?= $active_page === 'map' ? 'active' : 'link-light' ?>">
        <i class="fas fa-map-marked-alt me-2"></i>
          Map View
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>exports.php"
         class="nav-link <?= $active_page === 'exports' ? 'active' : 'link-light' ?>">
        <i class="fas fa-file-export me-2"></i>
          Export
      </a>
    </li>

    <li class="mt-2 mb-1 px-2">
      <small class="text-uppercase text-secondary fw-semibold">
          System
      </small>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>logs.php"
         class="nav-link <?= $active_page === 'logs' ? 'active' : 'link-light' ?>">
        <i class="fas fa-file-alt me-2"></i>
          Logs
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>scripts.php"
         class="nav-link <?= $active_page === 'scripts' ? 'active' : 'link-light' ?>">
        <i class="fas fa-terminal me-2"></i>
          Scripts
      </a>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>settings.php"
         class="nav-link <?= $active_page === 'settings' ? 'active' : 'link-light' ?>">
        <i class="fas fa-cogs me-2"></i>
          Settings
      </a>
    </li>

    <li class="mt-2 mb-1 px-2">
      <small class="text-uppercase text-secondary fw-semibold">
          <i class="fas fa-question-circle me-2"></i>
          Help
      </small>
    </li>
    <li class="nav-item">
      <a href="<?= $base ?>instructions.php"
         class="nav-link <?= $active_page === 'instructions' ? 'active' : 'link-light' ?>">
        <i class="fas fa-book me-2"></i>
          Instructions
      </a>
    </li>
  </ul>

  <hr class="border-secondary">
  <div class="text-secondary">
    v<?= h(APP_VERSION) ?> &nbsp;·&nbsp; <?= date('m/d/Y') ?>
  </div>
</nav>

<!-- ── Main content ──────────────────────────────────────────────────────── -->
<div id="page-content" class="flex-grow-1 overflow-auto">

  <!-- Top bar -->
  <div class="topbar d-flex align-items-center px-4 py-2 border-bottom border-secondary">
    <button class="btn btn-sm btn-outline-secondary me-3" id="sidebarToggle" title="Toggle sidebar">
      <i class="fas fa-bars"></i>
    </button>
    <h6 class="mb-0 fw-semibold">
        <?= h($page_title) ?>
    </h6>
    <div class="ms-auto d-flex align-items-center gap-2">
      <span id="db-status" class="badge bg-success" title="Database connected">
        <i class="fas fa-check me-1"></i>
          DB
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
