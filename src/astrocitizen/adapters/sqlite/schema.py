"""Schema SQLite — alinhado a MODELO_DADOS_V1 (subset S1+S2)."""

SCHEMA_VERSION = 8

# Tabelas S1 (v1)
SCHEMA_V1_SQL = """
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

# Tabelas S2 (v2) — targets, planos diarios, snapshots
SCHEMA_V2_SQL = """
CREATE TABLE IF NOT EXISTS targets (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    designation TEXT NOT NULL,
    ra_deg REAL,
    dec_deg REAL,
    target_type TEXT NOT NULL DEFAULT 'star',
    external_ids TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_targets_workspace_designation
    ON targets(workspace_id, designation) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS program_targets (
    program_id TEXT NOT NULL REFERENCES programs(id),
    target_id TEXT NOT NULL REFERENCES targets(id),
    role TEXT NOT NULL DEFAULT 'primary',
    sort_order INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (program_id, target_id, role)
);

CREATE TABLE IF NOT EXISTS daily_plans (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    site_id TEXT NOT NULL REFERENCES sites(id),
    night_date TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'draft',
    generated_at TEXT NOT NULL,
    published_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_plans_unique_night
    ON daily_plans(workspace_id, site_id, night_date) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS observation_blocks (
    id TEXT PRIMARY KEY,
    daily_plan_id TEXT NOT NULL REFERENCES daily_plans(id),
    program_id TEXT,
    target_id TEXT,
    instrument_config_id TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    window_start_utc TEXT NOT NULL,
    window_end_utc TEXT NOT NULL,
    predicted_altitude_deg REAL,
    airmass REAL,
    status TEXT NOT NULL DEFAULT 'candidato',
    status_reason TEXT,
    priority INTEGER NOT NULL DEFAULT 10,
    notes TEXT NOT NULL DEFAULT '',
    ephemeris_snapshot_id TEXT,
    meteo_snapshot_id TEXT,
    technique TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_blocks_plan_order
    ON observation_blocks(daily_plan_id, sort_order) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_blocks_plan_status
    ON observation_blocks(daily_plan_id, status) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS meteo_snapshots (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    site_id TEXT NOT NULL REFERENCES sites(id),
    captured_at_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS ephemeris_snapshots (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    site_id TEXT NOT NULL REFERENCES sites(id),
    target_id TEXT,
    epoch_utc TEXT NOT NULL,
    source TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}'
);
"""

# S3 — sessoes e eventos
SCHEMA_V3_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    site_id TEXT NOT NULL REFERENCES sites(id),
    daily_plan_id TEXT NOT NULL REFERENCES daily_plans(id),
    daily_plan_version INTEGER NOT NULL,
    device_id TEXT,
    started_at_utc TEXT NOT NULL,
    ended_at_utc TEXT,
    state TEXT NOT NULL DEFAULT 'active',
    plan_snapshot TEXT NOT NULL DEFAULT '{}',
    meteo_start_id TEXT,
    meteo_end_id TEXT,
    client_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_sessions_workspace_state
    ON sessions(workspace_id, state) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS session_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    block_id TEXT,
    event_type TEXT NOT NULL,
    occurred_at_utc TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    client_op_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_session_events_session
    ON session_events(session_id, occurred_at_utc);
"""

# S4/S5 — masters, produtos de analise, pontos
SCHEMA_V4_SQL = """
CREATE TABLE IF NOT EXISTS calibration_masters (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    kind TEXT NOT NULL,
    version_num INTEGER NOT NULL,
    artifact_id TEXT,
    parameters TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_masters_workspace_kind
    ON calibration_masters(workspace_id, kind, version_num) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS analysis_products (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    program_id TEXT,
    product_type TEXT NOT NULL,
    version_num INTEGER NOT NULL DEFAULT 1,
    parent_product_id TEXT,
    is_publishable INTEGER NOT NULL DEFAULT 0,
    parameters TEXT NOT NULL DEFAULT '{}',
    summary TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS analysis_product_observations (
    product_id TEXT NOT NULL REFERENCES analysis_products(id),
    observation_id TEXT NOT NULL REFERENCES observations(id),
    PRIMARY KEY (product_id, observation_id)
);

CREATE TABLE IF NOT EXISTS measurement_points (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES analysis_products(id),
    t_utc TEXT,
    sequence_index INTEGER,
    x REAL NOT NULL,
    y REAL NOT NULL,
    y_err REAL,
    band TEXT,
    meta TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_points_product
    ON measurement_points(product_id, sequence_index);
"""

SCHEMA_V5_SQL = """
CREATE TABLE IF NOT EXISTS network_submissions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    network TEXT NOT NULL,
    status TEXT NOT NULL,
    artifact_uri TEXT,
    product_id TEXT,
    payload_summary TEXT NOT NULL DEFAULT '{}',
    remote_ack TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_network_submissions_ws
    ON network_submissions(workspace_id, network, created_at) WHERE deleted_at IS NULL;
"""

SCHEMA_V6_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    trust_tier TEXT NOT NULL,
    license_id TEXT,
    lang TEXT,
    topics TEXT NOT NULL DEFAULT '[]',
    networks TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT,
    corpus_version TEXT,
    status TEXT NOT NULL DEFAULT 'planned',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_tier
    ON knowledge_documents(trust_tier) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status
    ON knowledge_documents(status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_lang
    ON knowledge_documents(lang) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES knowledge_documents(id),
    source_id TEXT NOT NULL,
    path TEXT,
    title TEXT,
    trust_tier TEXT NOT NULL,
    lang TEXT,
    topics TEXT NOT NULL DEFAULT '[]',
    po_id TEXT,
    network TEXT,
    pipeline_stage TEXT,
    token_estimate INTEGER,
    chunk_hash TEXT NOT NULL,
    corpus_version TEXT,
    body TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    deleted_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source
    ON knowledge_chunks(source_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_doc
    ON knowledge_chunks(document_id, sort_order) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_tier
    ON knowledge_chunks(trust_tier) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_filters
    ON knowledge_chunks(lang, po_id, network) WHERE deleted_at IS NULL;
"""

# AC-193: indice lexical FTS5 (rebuild via SqliteArchive.rebuild_knowledge_fts)
SCHEMA_V7_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    title,
    body,
    source_id UNINDEXED,
    trust_tier UNINDEXED,
    lang UNINDEXED,
    po_id UNINDEXED,
    network UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 2'
);
"""

# AC-195: embeddings locais (BLOB float32) para RRF hibrido
SCHEMA_V8_SQL = """
CREATE TABLE IF NOT EXISTS knowledge_chunk_embeddings (
    chunk_id TEXT PRIMARY KEY REFERENCES knowledge_chunks(id),
    model_id TEXT NOT NULL,
    dim INTEGER NOT NULL,
    vector BLOB NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_knowledge_emb_model
    ON knowledge_chunk_embeddings(model_id);
"""

SCHEMA_SQL = (
    SCHEMA_V1_SQL
    + SCHEMA_V2_SQL
    + SCHEMA_V3_SQL
    + SCHEMA_V4_SQL
    + SCHEMA_V5_SQL
    + SCHEMA_V6_SQL
    + SCHEMA_V7_SQL
    + SCHEMA_V8_SQL
)

# Colunas extra em observations (ALTER idempotente via migrate helper)
OBSERVATION_V3_COLUMNS = (
    ("session_id", "TEXT"),
    ("block_id", "TEXT"),
    ("target_id", "TEXT"),
    ("instrument_config_id", "TEXT"),
    ("meteo_snapshot_id", "TEXT"),
)
