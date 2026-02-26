<?php
/**
 * api/stats.php – Aggregated statistics.
 *
 * GET api/stats.php                   – full dashboard stats
 * GET api/stats.php?type=states       – record counts by state
 * GET api/stats.php?type=categories   – record counts by category
 * GET api/stats.php?type=formats      – source counts by format
 * GET api/stats.php?type=daily_runs   – runs per day (last 30 days)
 * GET api/stats.php?type=sources      – top sources by record count
 */
require_once dirname(__DIR__) . '/includes/functions.php';
require_method('GET');

$type = get_str('type');

switch ($type) {
    case 'states':
        $rows = db_all("
            SELECT state, COUNT(*) AS count
            FROM   raw_records
            WHERE  state IS NOT NULL
            GROUP  BY state ORDER BY count DESC");
        json_out(['states' => $rows]);

    case 'categories':
        $rows = db_all("
            SELECT category, COUNT(*) AS count
            FROM   raw_records
            WHERE  category IS NOT NULL
            GROUP  BY category ORDER BY count DESC");
        json_out(['categories' => $rows]);

    case 'formats':
        $rows = db_all("
            SELECT format, COUNT(*) AS count
            FROM   data_sources
            GROUP  BY format ORDER BY count DESC");
        json_out(['formats' => $rows]);

    case 'daily_runs':
        $days = max(7, min(90, get_int('days', 30)));
        $rows = db_all("
            SELECT DATE(started_at) AS day,
                   COUNT(*) AS total,
                   SUM(status='success') AS success,
                   SUM(status='failed')  AS failed,
                   SUM(status='partial') AS partial,
                   SUM(records_stored)   AS records_stored
            FROM   collection_runs
            WHERE  started_at >= DATE_SUB(CURDATE(), INTERVAL ? DAY)
            GROUP  BY day ORDER BY day",
            [$days]);
        json_out(['daily_runs' => $rows]);

    case 'sources':
        $rows = db_all("
            SELECT ds.source_id, ds.name, ds.state, ds.category, ds.format,
                   COUNT(rr.id) AS record_count,
                   MAX(cr.started_at) AS last_run
            FROM   data_sources ds
            LEFT   JOIN raw_records     rr ON rr.source_id = ds.id
            LEFT   JOIN collection_runs cr ON cr.source_id = ds.id
            GROUP  BY ds.id
            ORDER  BY record_count DESC LIMIT 20");
        json_out(['sources' => $rows]);

    default:
        // Full dashboard stats
        $stats = get_dashboard_stats();

        // Recent runs (last 24h)
        $recent = db_all("
            SELECT cr.id, cr.status, cr.records_stored, cr.started_at, cr.duration_seconds,
                   ds.name AS source_name, ds.state
            FROM   collection_runs cr
            JOIN   data_sources ds ON ds.id = cr.source_id
            WHERE  cr.started_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER  BY cr.started_at DESC LIMIT 20");

        // By state (top 10)
        $by_state = db_all("
            SELECT state, COUNT(*) AS count FROM raw_records
            WHERE state IS NOT NULL GROUP BY state ORDER BY count DESC LIMIT 10");

        // By category
        $by_cat = db_all("
            SELECT category, COUNT(*) AS count FROM raw_records
            WHERE category IS NOT NULL GROUP BY category ORDER BY count DESC");

        json_out([
            'stats'      => $stats,
            'recent_runs'=> $recent,
            'by_state'   => $by_state,
            'by_category'=> $by_cat,
        ]);
}
