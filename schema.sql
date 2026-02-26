-- Cannabis Data Aggregator - MySQL Schema
-- Run this once to create all tables.
-- Matches the SQLAlchemy models in src/storage/models.py

CREATE DATABASE IF NOT EXISTS cannabis_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cannabis_data;

-- ----------------------------------------------------------------
-- data_sources
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_sources (
    id                INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    source_id         VARCHAR(100)    NOT NULL,
    name              VARCHAR(255)    NOT NULL,
    description       TEXT            NULL,
    state             VARCHAR(20)     NOT NULL,
    agency            VARCHAR(255)    NULL,
    category          VARCHAR(50)     NOT NULL,
    subcategory       VARCHAR(50)     NULL,
    format            VARCHAR(20)     NOT NULL COMMENT 'soda | json | csv | geojson | xml',
    url               VARCHAR(2048)   NULL,
    discovery_url     VARCHAR(2048)   NULL,
    website           VARCHAR(2048)   NULL,
    enabled           TINYINT(1)      NOT NULL DEFAULT 1,
    api_key_required  TINYINT(1)      NOT NULL DEFAULT 0,
    api_key_env       VARCHAR(100)    NULL,
    params            JSON            NULL     COMMENT 'Default query params',
    headers           JSON            NULL     COMMENT 'Custom request headers',
    pagination        JSON            NULL     COMMENT 'Pagination config',
    field_mapping     JSON            NULL     COMMENT 'Field name mapping',
    tags              JSON            NULL     COMMENT 'List of tags',
    notes             TEXT            NULL,
    rate_limit_rpm    INT             NOT NULL DEFAULT 60,
    timeout           INT             NOT NULL DEFAULT 60,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_source_id (source_id),
    KEY ix_state      (state),
    KEY ix_category   (category),
    KEY ix_enabled    (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- collection_schedules
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collection_schedules (
    id                INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    schedule_id       VARCHAR(100)    NOT NULL,
    source_id         INT UNSIGNED    NOT NULL,
    name              VARCHAR(255)    NOT NULL,
    schedule_type     VARCHAR(20)     NOT NULL COMMENT 'interval | cron',
    enabled           TINYINT(1)      NOT NULL DEFAULT 1,
    priority          INT             NOT NULL DEFAULT 2 COMMENT '1=high 2=normal 3=low',
    cron_minute       VARCHAR(20)     NOT NULL DEFAULT '0',
    cron_hour         VARCHAR(20)     NOT NULL DEFAULT '0',
    cron_day_of_month VARCHAR(20)     NOT NULL DEFAULT '*',
    cron_month        VARCHAR(20)     NOT NULL DEFAULT '*',
    cron_day_of_week  VARCHAR(20)     NOT NULL DEFAULT '*',
    interval_value    INT             NULL,
    interval_unit     VARCHAR(20)     NULL COMMENT 'minutes | hours | days | weeks',
    notes             TEXT            NULL,
    next_run          DATETIME        NULL,
    last_run          DATETIME        NULL,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_schedule_id (schedule_id),
    KEY ix_source_id  (source_id),
    KEY ix_enabled    (enabled),
    CONSTRAINT fk_sched_source FOREIGN KEY (source_id) REFERENCES data_sources (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- collection_runs
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collection_runs (
    id                INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    source_id         INT UNSIGNED    NOT NULL,
    schedule_id       INT UNSIGNED    NULL,
    started_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at      DATETIME        NULL,
    status            VARCHAR(20)     NOT NULL COMMENT 'running | success | failed | partial | skipped',
    records_fetched   INT             NOT NULL DEFAULT 0,
    records_stored    INT             NOT NULL DEFAULT 0,
    records_updated   INT             NOT NULL DEFAULT 0,
    records_skipped   INT             NOT NULL DEFAULT 0,
    error_message     TEXT            NULL,
    raw_file_path     VARCHAR(512)    NULL,
    duration_seconds  DOUBLE          NULL,
    triggered_by      VARCHAR(50)     NOT NULL DEFAULT 'scheduler' COMMENT 'scheduler | manual | api',
    PRIMARY KEY (id),
    KEY ix_source_id  (source_id),
    KEY ix_schedule_id(schedule_id),
    KEY ix_started_at (started_at),
    KEY ix_status     (status),
    CONSTRAINT fk_run_source   FOREIGN KEY (source_id)   REFERENCES data_sources       (id) ON DELETE CASCADE,
    CONSTRAINT fk_run_schedule FOREIGN KEY (schedule_id) REFERENCES collection_schedules(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- raw_records
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_records (
    id               INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    source_id        INT UNSIGNED    NOT NULL,
    run_id           INT UNSIGNED    NULL,
    state            VARCHAR(5)      NULL,
    category         VARCHAR(50)     NULL,
    subcategory      VARCHAR(50)     NULL,
    name             VARCHAR(255)    NULL,
    license_number   VARCHAR(100)    NULL,
    license_type     VARCHAR(100)    NULL,
    license_status   VARCHAR(50)     NULL,
    address          VARCHAR(500)    NULL,
    city             VARCHAR(100)    NULL,
    zip_code         VARCHAR(20)     NULL,
    county           VARCHAR(100)    NULL,
    latitude         DOUBLE          NULL,
    longitude        DOUBLE          NULL,
    phone            VARCHAR(50)     NULL,
    email            VARCHAR(255)    NULL,
    website          VARCHAR(2048)   NULL,
    record_date      DATE            NULL,
    license_date     DATE            NULL,
    expiry_date      DATE            NULL,
    record_data      JSON            NOT NULL,
    record_hash      VARCHAR(64)     NULL,
    source_record_id VARCHAR(255)    NULL,
    created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_source_id        (source_id),
    KEY ix_run_id           (run_id),
    KEY ix_state            (state),
    KEY ix_category         (category),
    KEY ix_name             (name(191)),
    KEY ix_license_number   (license_number),
    KEY ix_license_type     (license_type),
    KEY ix_license_status   (license_status),
    KEY ix_city             (city),
    KEY ix_zip_code         (zip_code),
    KEY ix_county           (county),
    KEY ix_record_date      (record_date),
    KEY ix_created_at       (created_at),
    KEY ix_record_hash      (record_hash),
    KEY ix_state_category   (state, category),
    KEY ix_city_state       (city, state),
    CONSTRAINT fk_rec_source FOREIGN KEY (source_id) REFERENCES data_sources   (id) ON DELETE CASCADE,
    CONSTRAINT fk_rec_run    FOREIGN KEY (run_id)    REFERENCES collection_runs (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- collection_logs
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS collection_logs (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_id     INT UNSIGNED NULL,
    source_id  INT UNSIGNED NULL,
    level      VARCHAR(10)  NOT NULL COMMENT 'DEBUG | INFO | WARNING | ERROR',
    message    TEXT         NOT NULL,
    details    JSON         NULL,
    timestamp  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_run_id    (run_id),
    KEY ix_source_id (source_id),
    KEY ix_level     (level),
    KEY ix_timestamp (timestamp),
    CONSTRAINT fk_log_run    FOREIGN KEY (run_id)    REFERENCES collection_runs (id) ON DELETE SET NULL,
    CONSTRAINT fk_log_source FOREIGN KEY (source_id) REFERENCES data_sources   (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- app_settings
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_settings (
    id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    `key`       VARCHAR(100)  NOT NULL,
    value       TEXT          NULL,
    value_type  VARCHAR(20)   NOT NULL DEFAULT 'string' COMMENT 'string | int | float | bool | json',
    description VARCHAR(500)  NULL,
    category    VARCHAR(50)   NOT NULL DEFAULT 'general',
    updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_key (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------------
-- Default settings
-- ----------------------------------------------------------------
INSERT IGNORE INTO app_settings (`key`, value, value_type, description, category) VALUES
  ('collection_timeout',         '60',    'int',    'HTTP request timeout in seconds',            'collection'),
  ('collection_rate_limit_rpm',  '60',    'int',    'Default rate limit (requests per minute)',   'collection'),
  ('collection_max_retries',     '3',     'int',    'Max retry attempts on failure',              'collection'),
  ('collection_retry_delay',     '5',     'int',    'Seconds between retries',                    'collection'),
  ('storage_dedup_enabled',      'true',  'bool',   'Enable record deduplication',                'storage'),
  ('storage_max_records',        '0',     'int',    'Max records per source (0 = unlimited)',     'storage'),
  ('log_retention_days',         '90',    'int',    'Days to keep collection logs',               'logging'),
  ('log_level',                  'INFO',  'string', 'Minimum log level to store',                 'logging'),
  ('dashboard_records_per_page', '50',    'int',    'Records per page in the data browser',       'dashboard'),
  ('scheduler_enabled',          'true',  'bool',   'Enable background scheduler',                'scheduler');
