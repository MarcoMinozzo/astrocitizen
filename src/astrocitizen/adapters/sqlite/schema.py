"""Schema SQLite v1 (subset S1) — alinhado a MODELO_DADOS_V1."""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    name TEXT NOT NULL,
    latitude_deg REAL NOT NULL,
    longitude_deg REAL NOT NULL,
    elevation_m REAL NOT NULL DEFAULT 0,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    min_altitude_deg REAL NOT NULL DEFAULT 25.0,
    night_start_rule TEXT NOT NULL DEFAULT 'astronomical_twilight',
    meteo_thresholds TEXT NOT NULL DEFAULT '{}',
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_sites_workspace
    ON sites(workspace_id) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS equipment (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    backend TEXT,
    available INTEGER NOT NULL DEFAULT 1,
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_equipment_workspace
    ON equipment(workspace_id) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS instrument_configs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    name TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS instrument_config_items (
    config_id TEXT NOT NULL REFERENCES instrument_configs(id),
    equipment_id TEXT NOT NULL REFERENCES equipment(id),
    role TEXT NOT NULL,
    PRIMARY KEY (config_id, role)
);

CREATE TABLE IF NOT EXISTS program_templates (
    id TEXT PRIMARY KEY,
    class TEXT NOT NULL,
    name TEXT NOT NULL,
    technique TEXT NOT NULL DEFAULT '',
    default_networks TEXT NOT NULL DEFAULT '[]',
    minimum_product TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'P3',
    metadata TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS programs (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    template_id TEXT NOT NULL REFERENCES program_templates(id),
    name TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'draft',
    priority INTEGER NOT NULL DEFAULT 10,
    default_instrument_config_id TEXT,
    export_networks TEXT NOT NULL DEFAULT '[]',
    minimum_product TEXT NOT NULL DEFAULT '',
    cadence TEXT NOT NULL DEFAULT '{}',
    settings TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_programs_workspace_state
    ON programs(workspace_id, state) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    site_id TEXT,
    program_id TEXT,
    observed_at_utc TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'raw',
    camera_backend TEXT,
    simulated INTEGER NOT NULL DEFAULT 0,
    meteo_manual INTEGER NOT NULL DEFAULT 0,
    headers_summary TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_observations_workspace_sim
    ON observations(workspace_id, simulated) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    observation_id TEXT,
    kind TEXT NOT NULL,
    uri TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT,
    size_bytes INTEGER,
    content_type TEXT,
    immutable INTEGER NOT NULL DEFAULT 0,
    upload_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    at_utc TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_workspace_time
    ON audit_log(workspace_id, at_utc);
"""
