"""SqliteArchive — implementacao SQLite do ArchivePort (S1+S2)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.sqlite.schema import (
    OBSERVATION_V3_COLUMNS,
    SCHEMA_SQL,
    SCHEMA_VERSION,
)
from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.observatory.models import ObservationRecord, Session
from astrocitizen.planning.models import (
    DailyPlan,
    EphemerisSnapshot,
    MeteoSnapshot,
    ObservationBlock,
    Target,
)
from astrocitizen.programs.models import Program, ProgramTemplate
from astrocitizen.reduction.models import AnalysisProduct, CalibrationMaster
from astrocitizen.shared.errors import NotFoundError
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.timeutil import utc_now_iso
from astrocitizen.workspace.models import Workspace


def new_id_local():
    return new_id()


def _j(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _loads(raw: str | None, default: Any) -> Any:
    if raw is None or raw == "":
        return default
    return json.loads(raw)


class SqliteArchive:
    """ArchivePort sobre ficheiro SQLite (stdlib)."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> SqliteArchive:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def healthcheck(self) -> bool:
        try:
            row = self._conn.execute("SELECT 1").fetchone()
            return row is not None
        except sqlite3.Error:
            return False

    def migrate(self) -> int:
        self._conn.executescript(SCHEMA_SQL)
        self._ensure_observation_v3_columns()
        current = self._conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
        ).fetchone()[0]
        if current < SCHEMA_VERSION:
            self._conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, utc_now_iso()),
            )
            self._conn.commit()
            return SCHEMA_VERSION
        return int(current)

    def _ensure_observation_v3_columns(self) -> None:
        existing = {
            row[1]
            for row in self._conn.execute("PRAGMA table_info(observations)").fetchall()
        }
        for name, coltype in OBSERVATION_V3_COLUMNS:
            if name not in existing:
                self._conn.execute(f"ALTER TABLE observations ADD COLUMN {name} {coltype}")
        self._conn.commit()

    def _audit(
        self,
        action: str,
        entity_type: str,
        entity_id: str | None,
        workspace_id: str | None = None,
        detail: dict | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO audit_log(workspace_id, action, entity_type, entity_id, at_utc, detail)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                workspace_id,
                action,
                entity_type,
                entity_id,
                utc_now_iso(),
                _j(detail or {}),
            ),
        )

    def _soft_delete(self, table: str, entity_id: UUID, workspace_id: UUID | None = None) -> None:
        now = utc_now_iso()
        cur = self._conn.execute(
            f"UPDATE {table} SET deleted_at = ?, updated_at = ?, version = version + 1 "
            f"WHERE id = ? AND deleted_at IS NULL",
            (now, now, str(entity_id)),
        )
        if cur.rowcount == 0:
            raise NotFoundError(f"{table} nao encontrado: {entity_id}")
        ws = str(workspace_id) if workspace_id else None
        if ws is None:
            row = self._conn.execute(
                f"SELECT workspace_id FROM {table} WHERE id = ?", (str(entity_id),)
            ).fetchone()
            ws = row["workspace_id"] if row else None
        self._audit("soft_delete", table, str(entity_id), ws)
        self._conn.commit()

    # --- workspace ---
    def upsert_workspace(self, workspace: Workspace) -> Workspace:
        now = utc_now_iso()
        existing = self.get_workspace(workspace.id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO workspaces(id, name, created_at, updated_at, version)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(workspace.id), workspace.name, now, now, workspace.version),
            )
            self._audit("create", "workspaces", str(workspace.id), str(workspace.id))
        else:
            self._conn.execute(
                """
                UPDATE workspaces SET name = ?, updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (workspace.name, now, str(workspace.id)),
            )
            workspace.version = existing.version + 1
            self._audit("update", "workspaces", str(workspace.id), str(workspace.id))
        self._conn.commit()
        return workspace

    def get_workspace(self, workspace_id: UUID) -> Workspace | None:
        row = self._conn.execute(
            "SELECT * FROM workspaces WHERE id = ? AND deleted_at IS NULL",
            (str(workspace_id),),
        ).fetchone()
        if row is None:
            return None
        return Workspace(id=UUID(row["id"]), name=row["name"], version=row["version"])

    def list_workspaces(self) -> list[Workspace]:
        rows = self._conn.execute(
            "SELECT * FROM workspaces WHERE deleted_at IS NULL ORDER BY name"
        ).fetchall()
        return [Workspace(id=UUID(r["id"]), name=r["name"], version=r["version"]) for r in rows]

    # --- sites ---
    def upsert_site(self, site: Site) -> Site:
        now = utc_now_iso()
        existing = self.get_site(site.id)
        if site.is_default:
            self._conn.execute(
                "UPDATE sites SET is_default = 0 WHERE workspace_id = ? AND deleted_at IS NULL",
                (str(site.workspace_id),),
            )
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO sites(
                    id, workspace_id, name, latitude_deg, longitude_deg, elevation_m, timezone,
                    min_altitude_deg, night_start_rule, meteo_thresholds, is_default,
                    created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(site.id),
                    str(site.workspace_id),
                    site.name,
                    site.latitude_deg,
                    site.longitude_deg,
                    site.elevation_m,
                    site.timezone,
                    site.min_altitude_deg,
                    site.night_start_rule,
                    _j(site.meteo_thresholds),
                    1 if site.is_default else 0,
                    now,
                    now,
                    site.version,
                ),
            )
            self._audit("create", "sites", str(site.id), str(site.workspace_id))
        else:
            self._conn.execute(
                """
                UPDATE sites SET
                    name = ?, latitude_deg = ?, longitude_deg = ?, elevation_m = ?,
                    timezone = ?, min_altitude_deg = ?, night_start_rule = ?,
                    meteo_thresholds = ?, is_default = ?, updated_at = ?,
                    version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    site.name,
                    site.latitude_deg,
                    site.longitude_deg,
                    site.elevation_m,
                    site.timezone,
                    site.min_altitude_deg,
                    site.night_start_rule,
                    _j(site.meteo_thresholds),
                    1 if site.is_default else 0,
                    now,
                    str(site.id),
                ),
            )
            site.version = existing.version + 1
            self._audit("update", "sites", str(site.id), str(site.workspace_id))
        self._conn.commit()
        return site

    def _row_to_site(self, row: sqlite3.Row) -> Site:
        return Site(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            name=row["name"],
            latitude_deg=row["latitude_deg"],
            longitude_deg=row["longitude_deg"],
            elevation_m=row["elevation_m"],
            timezone=row["timezone"],
            min_altitude_deg=row["min_altitude_deg"],
            night_start_rule=row["night_start_rule"],
            meteo_thresholds=_loads(row["meteo_thresholds"], {}),
            is_default=bool(row["is_default"]),
            version=row["version"],
        )

    def get_site(self, site_id: UUID) -> Site | None:
        row = self._conn.execute(
            "SELECT * FROM sites WHERE id = ? AND deleted_at IS NULL",
            (str(site_id),),
        ).fetchone()
        return None if row is None else self._row_to_site(row)

    def list_sites(self, workspace_id: UUID) -> list[Site]:
        rows = self._conn.execute(
            """
            SELECT * FROM sites
            WHERE workspace_id = ? AND deleted_at IS NULL
            ORDER BY is_default DESC, name
            """,
            (str(workspace_id),),
        ).fetchall()
        return [self._row_to_site(r) for r in rows]

    def soft_delete_site(self, site_id: UUID) -> None:
        self._soft_delete("sites", site_id)

    # --- equipment ---
    def upsert_equipment(self, equipment: Equipment) -> Equipment:
        now = utc_now_iso()
        existing = self.get_equipment(equipment.id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO equipment(
                    id, workspace_id, type, name, backend, available, metadata,
                    created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(equipment.id),
                    str(equipment.workspace_id),
                    equipment.type,
                    equipment.name,
                    equipment.backend,
                    1 if equipment.available else 0,
                    _j(equipment.metadata),
                    now,
                    now,
                    equipment.version,
                ),
            )
            self._audit("create", "equipment", str(equipment.id), str(equipment.workspace_id))
        else:
            self._conn.execute(
                """
                UPDATE equipment SET
                    type = ?, name = ?, backend = ?, available = ?, metadata = ?,
                    updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    equipment.type,
                    equipment.name,
                    equipment.backend,
                    1 if equipment.available else 0,
                    _j(equipment.metadata),
                    now,
                    str(equipment.id),
                ),
            )
            equipment.version = existing.version + 1
            self._audit("update", "equipment", str(equipment.id), str(equipment.workspace_id))
        self._conn.commit()
        return equipment

    def _row_to_equipment(self, row: sqlite3.Row) -> Equipment:
        return Equipment(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            type=row["type"],
            name=row["name"],
            backend=row["backend"],
            available=bool(row["available"]),
            metadata=_loads(row["metadata"], {}),
            version=row["version"],
        )

    def get_equipment(self, equipment_id: UUID) -> Equipment | None:
        row = self._conn.execute(
            "SELECT * FROM equipment WHERE id = ? AND deleted_at IS NULL",
            (str(equipment_id),),
        ).fetchone()
        return None if row is None else self._row_to_equipment(row)

    def list_equipment(self, workspace_id: UUID) -> list[Equipment]:
        rows = self._conn.execute(
            """
            SELECT * FROM equipment
            WHERE workspace_id = ? AND deleted_at IS NULL
            ORDER BY type, name
            """,
            (str(workspace_id),),
        ).fetchall()
        return [self._row_to_equipment(r) for r in rows]

    def soft_delete_equipment(self, equipment_id: UUID) -> None:
        self._soft_delete("equipment", equipment_id)

    # --- instrument configs ---
    def upsert_instrument_config(self, config: InstrumentConfig) -> InstrumentConfig:
        now = utc_now_iso()
        existing = self.get_instrument_config(config.id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO instrument_configs(
                    id, workspace_id, name, notes, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(config.id),
                    str(config.workspace_id),
                    config.name,
                    config.notes,
                    now,
                    now,
                    config.version,
                ),
            )
            self._audit(
                "create", "instrument_configs", str(config.id), str(config.workspace_id)
            )
        else:
            self._conn.execute(
                """
                UPDATE instrument_configs SET
                    name = ?, notes = ?, updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (config.name, config.notes, now, str(config.id)),
            )
            config.version = existing.version + 1
            self._conn.execute(
                "DELETE FROM instrument_config_items WHERE config_id = ?",
                (str(config.id),),
            )
            self._audit(
                "update", "instrument_configs", str(config.id), str(config.workspace_id)
            )
        for role, eq_id in config.items.items():
            self._conn.execute(
                """
                INSERT INTO instrument_config_items(config_id, equipment_id, role)
                VALUES (?, ?, ?)
                """,
                (str(config.id), str(eq_id), role),
            )
        self._conn.commit()
        return config

    def get_instrument_config(self, config_id: UUID) -> InstrumentConfig | None:
        row = self._conn.execute(
            "SELECT * FROM instrument_configs WHERE id = ? AND deleted_at IS NULL",
            (str(config_id),),
        ).fetchone()
        if row is None:
            return None
        items = self._conn.execute(
            "SELECT role, equipment_id FROM instrument_config_items WHERE config_id = ?",
            (str(config_id),),
        ).fetchall()
        return InstrumentConfig(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            name=row["name"],
            notes=row["notes"],
            items={r["role"]: UUID(r["equipment_id"]) for r in items},
            version=row["version"],
        )

    def list_instrument_configs(self, workspace_id: UUID) -> list[InstrumentConfig]:
        rows = self._conn.execute(
            """
            SELECT id FROM instrument_configs
            WHERE workspace_id = ? AND deleted_at IS NULL
            ORDER BY name
            """,
            (str(workspace_id),),
        ).fetchall()
        result: list[InstrumentConfig] = []
        for r in rows:
            cfg = self.get_instrument_config(UUID(r["id"]))
            if cfg is not None:
                result.append(cfg)
        return result

    # --- templates ---
    def upsert_program_template(self, template: ProgramTemplate) -> ProgramTemplate:
        self._conn.execute(
            """
            INSERT INTO program_templates(
                id, class, name, technique, default_networks, minimum_product, priority, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                class = excluded.class,
                name = excluded.name,
                technique = excluded.technique,
                default_networks = excluded.default_networks,
                minimum_product = excluded.minimum_product,
                priority = excluded.priority,
                metadata = excluded.metadata
            """,
            (
                template.id,
                template.class_,
                template.name,
                template.technique,
                _j(template.default_networks),
                template.minimum_product,
                template.priority,
                _j(template.metadata),
            ),
        )
        self._conn.commit()
        return template

    def _row_to_template(self, row: sqlite3.Row) -> ProgramTemplate:
        return ProgramTemplate(
            id=row["id"],
            class_=row["class"],
            name=row["name"],
            technique=row["technique"],
            default_networks=_loads(row["default_networks"], []),
            minimum_product=row["minimum_product"],
            priority=row["priority"],
            metadata=_loads(row["metadata"], {}),
        )

    def get_program_template(self, template_id: str) -> ProgramTemplate | None:
        row = self._conn.execute(
            "SELECT * FROM program_templates WHERE id = ?",
            (template_id,),
        ).fetchone()
        return None if row is None else self._row_to_template(row)

    def list_program_templates(self, *, class_: str | None = None) -> list[ProgramTemplate]:
        if class_:
            rows = self._conn.execute(
                "SELECT * FROM program_templates WHERE class = ? ORDER BY id",
                (class_,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM program_templates ORDER BY id"
            ).fetchall()
        return [self._row_to_template(r) for r in rows]

    # --- programs ---
    def upsert_program(self, program: Program) -> Program:
        now = utc_now_iso()
        existing = self.get_program(program.id)
        cfg_id = (
            str(program.default_instrument_config_id)
            if program.default_instrument_config_id
            else None
        )
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO programs(
                    id, workspace_id, template_id, name, state, priority,
                    default_instrument_config_id, export_networks, minimum_product,
                    cadence, settings, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(program.id),
                    str(program.workspace_id),
                    program.template_id,
                    program.name,
                    program.state,
                    program.priority,
                    cfg_id,
                    _j(program.export_networks),
                    program.minimum_product,
                    _j(program.cadence),
                    _j(program.settings),
                    now,
                    now,
                    program.version,
                ),
            )
            self._audit("create", "programs", str(program.id), str(program.workspace_id))
        else:
            self._conn.execute(
                """
                UPDATE programs SET
                    template_id = ?, name = ?, state = ?, priority = ?,
                    default_instrument_config_id = ?, export_networks = ?,
                    minimum_product = ?, cadence = ?, settings = ?,
                    updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    program.template_id,
                    program.name,
                    program.state,
                    program.priority,
                    cfg_id,
                    _j(program.export_networks),
                    program.minimum_product,
                    _j(program.cadence),
                    _j(program.settings),
                    now,
                    str(program.id),
                ),
            )
            program.version = existing.version + 1
            self._audit("update", "programs", str(program.id), str(program.workspace_id))
        self._conn.commit()
        return program

    def _row_to_program(self, row: sqlite3.Row) -> Program:
        cfg = row["default_instrument_config_id"]
        return Program(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            template_id=row["template_id"],
            name=row["name"],
            state=row["state"],
            priority=row["priority"],
            default_instrument_config_id=UUID(cfg) if cfg else None,
            export_networks=_loads(row["export_networks"], []),
            minimum_product=row["minimum_product"],
            cadence=_loads(row["cadence"], {}),
            settings=_loads(row["settings"], {}),
            version=row["version"],
        )

    def get_program(self, program_id: UUID) -> Program | None:
        row = self._conn.execute(
            "SELECT * FROM programs WHERE id = ? AND deleted_at IS NULL",
            (str(program_id),),
        ).fetchone()
        return None if row is None else self._row_to_program(row)

    def list_programs(self, workspace_id: UUID, *, state: str | None = None) -> list[Program]:
        if state:
            rows = self._conn.execute(
                """
                SELECT * FROM programs
                WHERE workspace_id = ? AND state = ? AND deleted_at IS NULL
                ORDER BY priority, name
                """,
                (str(workspace_id), state),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM programs
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY priority, name
                """,
                (str(workspace_id),),
            ).fetchall()
        return [self._row_to_program(r) for r in rows]

    def soft_delete_program(self, program_id: UUID) -> None:
        self._soft_delete("programs", program_id)

    # --- observations ---
    def create_observation(
        self,
        *,
        observation_id: UUID,
        workspace_id: UUID,
        observed_at_utc: str,
        site_id: UUID | None = None,
        program_id: UUID | None = None,
        simulated: bool = False,
        notes: str = "",
    ) -> UUID:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO observations(
                id, workspace_id, site_id, program_id, observed_at_utc, state,
                simulated, notes, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, 'raw', ?, ?, ?, ?, 1)
            """,
            (
                str(observation_id),
                str(workspace_id),
                str(site_id) if site_id else None,
                str(program_id) if program_id else None,
                observed_at_utc,
                1 if simulated else 0,
                notes,
                now,
                now,
            ),
        )
        self._audit(
            "create",
            "observations",
            str(observation_id),
            str(workspace_id),
            {"simulated": simulated},
        )
        self._conn.commit()
        return observation_id

    def list_observations(
        self,
        workspace_id: UUID,
        *,
        include_simulated: bool = False,
    ) -> list[dict]:
        if include_simulated:
            rows = self._conn.execute(
                """
                SELECT * FROM observations
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY observed_at_utc DESC
                """,
                (str(workspace_id),),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM observations
                WHERE workspace_id = ? AND deleted_at IS NULL AND simulated = 0
                ORDER BY observed_at_utc DESC
                """,
                (str(workspace_id),),
            ).fetchall()
        return [dict(r) for r in rows]

    def soft_delete_observation(self, observation_id: UUID) -> None:
        self._soft_delete("observations", observation_id)

    def list_audit(
        self,
        workspace_id: UUID | None = None,
        *,
        limit: int = 100,
    ) -> list[dict]:
        if workspace_id is None:
            rows = self._conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM audit_log
                WHERE workspace_id = ?
                ORDER BY id DESC LIMIT ?
                """,
                (str(workspace_id), limit),
            ).fetchall()
        return [dict(r) for r in rows]

    # --- targets (S2) ---
    def upsert_target(self, target: Target) -> Target:
        now = utc_now_iso()
        existing = self.get_target(target.id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO targets(
                    id, workspace_id, designation, ra_deg, dec_deg, target_type,
                    external_ids, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(target.id),
                    str(target.workspace_id),
                    target.designation,
                    target.ra_deg,
                    target.dec_deg,
                    target.target_type,
                    _j(target.external_ids),
                    now,
                    now,
                    target.version,
                ),
            )
            self._audit("create", "targets", str(target.id), str(target.workspace_id))
        else:
            self._conn.execute(
                """
                UPDATE targets SET
                    designation = ?, ra_deg = ?, dec_deg = ?, target_type = ?,
                    external_ids = ?, updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    target.designation,
                    target.ra_deg,
                    target.dec_deg,
                    target.target_type,
                    _j(target.external_ids),
                    now,
                    str(target.id),
                ),
            )
            target.version = existing.version + 1
            self._audit("update", "targets", str(target.id), str(target.workspace_id))
        self._conn.commit()
        return target

    def _row_to_target(self, row: sqlite3.Row) -> Target:
        return Target(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            designation=row["designation"],
            ra_deg=row["ra_deg"],
            dec_deg=row["dec_deg"],
            target_type=row["target_type"],
            external_ids=_loads(row["external_ids"], {}),
            version=row["version"],
        )

    def get_target(self, target_id: UUID) -> Target | None:
        row = self._conn.execute(
            "SELECT * FROM targets WHERE id = ? AND deleted_at IS NULL",
            (str(target_id),),
        ).fetchone()
        return None if row is None else self._row_to_target(row)

    def list_targets(self, workspace_id: UUID) -> list[Target]:
        rows = self._conn.execute(
            """
            SELECT * FROM targets
            WHERE workspace_id = ? AND deleted_at IS NULL
            ORDER BY designation
            """,
            (str(workspace_id),),
        ).fetchall()
        return [self._row_to_target(r) for r in rows]

    def soft_delete_target(self, target_id: UUID) -> None:
        self._soft_delete("targets", target_id)

    def link_program_target(
        self,
        program_id: UUID,
        target_id: UUID,
        *,
        role: str = "primary",
        sort_order: int = 0,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO program_targets(program_id, target_id, role, sort_order)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(program_id, target_id, role) DO UPDATE SET sort_order = excluded.sort_order
            """,
            (str(program_id), str(target_id), role, sort_order),
        )
        self._conn.commit()

    def list_program_targets(self, program_id: UUID) -> list[tuple[Target, str, int]]:
        rows = self._conn.execute(
            """
            SELECT t.*, pt.role, pt.sort_order
            FROM program_targets pt
            JOIN targets t ON t.id = pt.target_id
            WHERE pt.program_id = ? AND t.deleted_at IS NULL
            ORDER BY pt.sort_order, t.designation
            """,
            (str(program_id),),
        ).fetchall()
        return [(self._row_to_target(r), r["role"], int(r["sort_order"])) for r in rows]

    # --- daily plans ---
    def upsert_daily_plan(self, plan: DailyPlan) -> DailyPlan:
        now = utc_now_iso()
        existing = self.get_daily_plan(plan.id)
        generated = plan.generated_at or now
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO daily_plans(
                    id, workspace_id, site_id, night_date, state, generated_at,
                    published_at, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(plan.id),
                    str(plan.workspace_id),
                    str(plan.site_id),
                    plan.night_date,
                    plan.state,
                    generated,
                    plan.published_at,
                    now,
                    now,
                    plan.version,
                ),
            )
            plan.generated_at = generated
            self._audit("create", "daily_plans", str(plan.id), str(plan.workspace_id))
        else:
            self._conn.execute(
                """
                UPDATE daily_plans SET
                    state = ?, generated_at = ?, published_at = ?,
                    updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    plan.state,
                    generated,
                    plan.published_at,
                    now,
                    str(plan.id),
                ),
            )
            plan.generated_at = generated
            plan.version = existing.version + 1
            self._audit("update", "daily_plans", str(plan.id), str(plan.workspace_id))
        self._conn.commit()
        return plan

    def _row_to_plan(self, row: sqlite3.Row) -> DailyPlan:
        return DailyPlan(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            site_id=UUID(row["site_id"]),
            night_date=row["night_date"],
            state=row["state"],
            generated_at=row["generated_at"],
            published_at=row["published_at"],
            version=row["version"],
        )

    def get_daily_plan(self, plan_id: UUID) -> DailyPlan | None:
        row = self._conn.execute(
            "SELECT * FROM daily_plans WHERE id = ? AND deleted_at IS NULL",
            (str(plan_id),),
        ).fetchone()
        return None if row is None else self._row_to_plan(row)

    def get_daily_plan_for_night(
        self,
        workspace_id: UUID,
        site_id: UUID,
        night_date: str,
    ) -> DailyPlan | None:
        row = self._conn.execute(
            """
            SELECT * FROM daily_plans
            WHERE workspace_id = ? AND site_id = ? AND night_date = ?
              AND deleted_at IS NULL
            """,
            (str(workspace_id), str(site_id), night_date),
        ).fetchone()
        return None if row is None else self._row_to_plan(row)

    def list_daily_plans(
        self, workspace_id: UUID, *, site_id: UUID | None = None
    ) -> list[DailyPlan]:
        if site_id is None:
            rows = self._conn.execute(
                """
                SELECT * FROM daily_plans
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY night_date DESC
                """,
                (str(workspace_id),),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM daily_plans
                WHERE workspace_id = ? AND site_id = ? AND deleted_at IS NULL
                ORDER BY night_date DESC
                """,
                (str(workspace_id), str(site_id)),
            ).fetchall()
        return [self._row_to_plan(r) for r in rows]

    def _row_to_block(self, row: sqlite3.Row) -> ObservationBlock:
        def _uuid(val: str | None) -> UUID | None:
            return UUID(val) if val else None

        return ObservationBlock(
            id=UUID(row["id"]),
            daily_plan_id=UUID(row["daily_plan_id"]),
            program_id=_uuid(row["program_id"]),
            target_id=_uuid(row["target_id"]),
            instrument_config_id=_uuid(row["instrument_config_id"]),
            sort_order=row["sort_order"],
            window_start_utc=row["window_start_utc"],
            window_end_utc=row["window_end_utc"],
            predicted_altitude_deg=row["predicted_altitude_deg"],
            airmass=row["airmass"],
            status=row["status"],
            status_reason=row["status_reason"],
            priority=row["priority"],
            notes=row["notes"] or "",
            ephemeris_snapshot_id=_uuid(row["ephemeris_snapshot_id"]),
            meteo_snapshot_id=_uuid(row["meteo_snapshot_id"]),
            technique=row["technique"],
            version=row["version"],
        )

    def replace_observation_blocks(
        self,
        daily_plan_id: UUID,
        blocks: list[ObservationBlock],
    ) -> list[ObservationBlock]:
        now = utc_now_iso()
        self._conn.execute(
            """
            UPDATE observation_blocks
            SET deleted_at = ?, updated_at = ?
            WHERE daily_plan_id = ? AND deleted_at IS NULL
            """,
            (now, now, str(daily_plan_id)),
        )
        for block in blocks:
            self._conn.execute(
                """
                INSERT INTO observation_blocks(
                    id, daily_plan_id, program_id, target_id, instrument_config_id,
                    sort_order, window_start_utc, window_end_utc,
                    predicted_altitude_deg, airmass, status, status_reason, priority,
                    notes, ephemeris_snapshot_id, meteo_snapshot_id, technique,
                    created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(block.id),
                    str(daily_plan_id),
                    str(block.program_id) if block.program_id else None,
                    str(block.target_id) if block.target_id else None,
                    str(block.instrument_config_id) if block.instrument_config_id else None,
                    block.sort_order,
                    block.window_start_utc,
                    block.window_end_utc,
                    block.predicted_altitude_deg,
                    block.airmass,
                    block.status,
                    block.status_reason,
                    block.priority,
                    block.notes,
                    str(block.ephemeris_snapshot_id) if block.ephemeris_snapshot_id else None,
                    str(block.meteo_snapshot_id) if block.meteo_snapshot_id else None,
                    block.technique,
                    now,
                    now,
                    block.version,
                ),
            )
        self._audit("replace_blocks", "daily_plans", str(daily_plan_id), detail={"n": len(blocks)})
        self._conn.commit()
        return blocks

    def add_observation_block(self, block: ObservationBlock) -> ObservationBlock:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO observation_blocks(
                id, daily_plan_id, program_id, target_id, instrument_config_id,
                sort_order, window_start_utc, window_end_utc,
                predicted_altitude_deg, airmass, status, status_reason, priority,
                notes, ephemeris_snapshot_id, meteo_snapshot_id, technique,
                created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(block.id),
                str(block.daily_plan_id),
                str(block.program_id) if block.program_id else None,
                str(block.target_id) if block.target_id else None,
                str(block.instrument_config_id) if block.instrument_config_id else None,
                block.sort_order,
                block.window_start_utc,
                block.window_end_utc,
                block.predicted_altitude_deg,
                block.airmass,
                block.status,
                block.status_reason,
                block.priority,
                block.notes,
                str(block.ephemeris_snapshot_id) if block.ephemeris_snapshot_id else None,
                str(block.meteo_snapshot_id) if block.meteo_snapshot_id else None,
                block.technique,
                now,
                now,
                block.version,
            ),
        )
        self._audit("create", "observation_blocks", str(block.id))
        self._conn.commit()
        return block

    def list_observation_blocks(self, daily_plan_id: UUID) -> list[ObservationBlock]:
        rows = self._conn.execute(
            """
            SELECT * FROM observation_blocks
            WHERE daily_plan_id = ? AND deleted_at IS NULL
            ORDER BY sort_order, priority
            """,
            (str(daily_plan_id),),
        ).fetchall()
        return [self._row_to_block(r) for r in rows]

    def get_observation_block(self, block_id: UUID) -> ObservationBlock | None:
        row = self._conn.execute(
            "SELECT * FROM observation_blocks WHERE id = ? AND deleted_at IS NULL",
            (str(block_id),),
        ).fetchone()
        return None if row is None else self._row_to_block(row)

    def update_observation_block(self, block: ObservationBlock) -> ObservationBlock:
        now = utc_now_iso()
        existing = self.get_observation_block(block.id)
        if existing is None:
            raise NotFoundError(f"observation_blocks nao encontrado: {block.id}")
        self._conn.execute(
            """
            UPDATE observation_blocks SET
                sort_order = ?, status = ?, status_reason = ?, notes = ?,
                priority = ?, updated_at = ?, version = version + 1
            WHERE id = ? AND deleted_at IS NULL
            """,
            (
                block.sort_order,
                block.status,
                block.status_reason,
                block.notes,
                block.priority,
                now,
                str(block.id),
            ),
        )
        block.version = existing.version + 1
        self._audit("update", "observation_blocks", str(block.id))
        self._conn.commit()
        return block

    def save_meteo_snapshot(self, snap: MeteoSnapshot) -> MeteoSnapshot:
        self._conn.execute(
            """
            INSERT INTO meteo_snapshots(id, workspace_id, site_id, captured_at_utc, source, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(snap.id),
                str(snap.workspace_id),
                str(snap.site_id),
                snap.captured_at_utc,
                snap.source,
                _j(snap.payload),
            ),
        )
        self._conn.commit()
        return snap

    def save_ephemeris_snapshot(self, snap: EphemerisSnapshot) -> EphemerisSnapshot:
        self._conn.execute(
            """
            INSERT INTO ephemeris_snapshots(
                id, workspace_id, site_id, target_id, epoch_utc, source, payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(snap.id),
                str(snap.workspace_id),
                str(snap.site_id),
                str(snap.target_id) if snap.target_id else None,
                snap.epoch_utc,
                snap.source,
                _j(snap.payload),
            ),
        )
        self._conn.commit()
        return snap

    # --- sessions (S3) ---
    def upsert_session(self, session: Session) -> Session:
        now = utc_now_iso()
        existing = self.get_session(session.id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO sessions(
                    id, workspace_id, site_id, daily_plan_id, daily_plan_version,
                    device_id, started_at_utc, ended_at_utc, state, plan_snapshot,
                    meteo_start_id, meteo_end_id, client_id, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(session.id),
                    str(session.workspace_id),
                    str(session.site_id),
                    str(session.daily_plan_id),
                    session.daily_plan_version,
                    str(session.device_id) if session.device_id else None,
                    session.started_at_utc,
                    session.ended_at_utc,
                    session.state,
                    _j(session.plan_snapshot),
                    str(session.meteo_start_id) if session.meteo_start_id else None,
                    str(session.meteo_end_id) if session.meteo_end_id else None,
                    str(session.client_id) if session.client_id else None,
                    now,
                    now,
                    session.version,
                ),
            )
            self._audit("create", "sessions", str(session.id), str(session.workspace_id))
        else:
            self._conn.execute(
                """
                UPDATE sessions SET
                    state = ?, ended_at_utc = ?, plan_snapshot = ?,
                    meteo_start_id = ?, meteo_end_id = ?,
                    updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    session.state,
                    session.ended_at_utc,
                    _j(session.plan_snapshot),
                    str(session.meteo_start_id) if session.meteo_start_id else None,
                    str(session.meteo_end_id) if session.meteo_end_id else None,
                    now,
                    str(session.id),
                ),
            )
            session.version = existing.version + 1
            self._audit("update", "sessions", str(session.id), str(session.workspace_id))
        self._conn.commit()
        return session

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        def _u(val: str | None) -> UUID | None:
            return UUID(val) if val else None

        return Session(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            site_id=UUID(row["site_id"]),
            daily_plan_id=UUID(row["daily_plan_id"]),
            daily_plan_version=row["daily_plan_version"],
            started_at_utc=row["started_at_utc"],
            ended_at_utc=row["ended_at_utc"],
            state=row["state"],
            plan_snapshot=_loads(row["plan_snapshot"], {}),
            meteo_start_id=_u(row["meteo_start_id"]),
            meteo_end_id=_u(row["meteo_end_id"]),
            device_id=_u(row["device_id"]),
            client_id=_u(row["client_id"]),
            version=row["version"],
        )

    def get_session(self, session_id: UUID) -> Session | None:
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE id = ? AND deleted_at IS NULL",
            (str(session_id),),
        ).fetchone()
        return None if row is None else self._row_to_session(row)

    def list_sessions(self, workspace_id: UUID, *, state: str | None = None) -> list[Session]:
        if state:
            rows = self._conn.execute(
                """
                SELECT * FROM sessions
                WHERE workspace_id = ? AND state = ? AND deleted_at IS NULL
                ORDER BY started_at_utc DESC
                """,
                (str(workspace_id), state),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM sessions
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY started_at_utc DESC
                """,
                (str(workspace_id),),
            ).fetchall()
        return [self._row_to_session(r) for r in rows]

    def add_session_event(
        self,
        *,
        event_id: UUID,
        session_id: UUID,
        event_type: str,
        occurred_at_utc: str,
        block_id: UUID | None = None,
        payload: dict | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO session_events(
                id, session_id, block_id, event_type, occurred_at_utc, payload
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(event_id),
                str(session_id),
                str(block_id) if block_id else None,
                event_type,
                occurred_at_utc,
                _j(payload or {}),
            ),
        )
        self._conn.commit()

    def save_observation(self, obs: ObservationRecord) -> ObservationRecord:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO observations(
                id, workspace_id, site_id, program_id, observed_at_utc, state,
                camera_backend, simulated, meteo_manual, headers_summary, notes,
                session_id, block_id, target_id, instrument_config_id, meteo_snapshot_id,
                created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(obs.id),
                str(obs.workspace_id),
                str(obs.site_id) if obs.site_id else None,
                str(obs.program_id) if obs.program_id else None,
                obs.observed_at_utc,
                obs.state,
                obs.camera_backend,
                1 if obs.simulated else 0,
                1 if obs.meteo_manual else 0,
                _j(obs.headers_summary),
                obs.notes,
                str(obs.session_id) if obs.session_id else None,
                str(obs.block_id) if obs.block_id else None,
                str(obs.target_id) if obs.target_id else None,
                str(obs.instrument_config_id) if obs.instrument_config_id else None,
                str(obs.meteo_snapshot_id) if obs.meteo_snapshot_id else None,
                now,
                now,
                obs.version,
            ),
        )
        self._audit(
            "create",
            "observations",
            str(obs.id),
            str(obs.workspace_id),
            {"simulated": obs.simulated, "backend": obs.camera_backend},
        )
        self._conn.commit()
        return obs

    def save_artifact(
        self,
        *,
        artifact_id: UUID,
        workspace_id: UUID,
        kind: str,
        uri: str,
        filename: str,
        observation_id: UUID | None = None,
        size_bytes: int | None = None,
    ) -> UUID:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO artifacts(
                id, workspace_id, observation_id, kind, uri, filename,
                size_bytes, immutable, upload_status, created_at, updated_at, version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'local', ?, ?, 1)
            """,
            (
                str(artifact_id),
                str(workspace_id),
                str(observation_id) if observation_id else None,
                kind,
                uri,
                filename,
                size_bytes,
                now,
                now,
            ),
        )
        self._conn.commit()
        return artifact_id

    # --- reduction / analysis (S4/S5) ---
    def save_calibration_master(self, master: CalibrationMaster) -> CalibrationMaster:
        self._conn.execute(
            """
            INSERT INTO calibration_masters(
                id, workspace_id, kind, version_num, artifact_id, parameters, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(master.id),
                str(master.workspace_id),
                master.kind,
                master.version_num,
                str(master.artifact_id) if master.artifact_id else None,
                _j(master.parameters),
                master.notes,
                master.created_at or utc_now_iso(),
            ),
        )
        self._conn.commit()
        return master

    def get_calibration_master(self, master_id: UUID) -> CalibrationMaster | None:
        row = self._conn.execute(
            "SELECT * FROM calibration_masters WHERE id = ? AND deleted_at IS NULL",
            (str(master_id),),
        ).fetchone()
        if row is None:
            return None
        return CalibrationMaster(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            kind=row["kind"],
            version_num=row["version_num"],
            artifact_id=UUID(row["artifact_id"]) if row["artifact_id"] else None,
            parameters=_loads(row["parameters"], {}),
            notes=row["notes"] or "",
            created_at=row["created_at"],
        )

    def list_calibration_masters(
        self, workspace_id: UUID, *, kind: str | None = None
    ) -> list[CalibrationMaster]:
        if kind:
            rows = self._conn.execute(
                """
                SELECT * FROM calibration_masters
                WHERE workspace_id = ? AND kind = ? AND deleted_at IS NULL
                ORDER BY version_num DESC
                """,
                (str(workspace_id), kind),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM calibration_masters
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY kind, version_num DESC
                """,
                (str(workspace_id),),
            ).fetchall()
        out: list[CalibrationMaster] = []
        for row in rows:
            out.append(
                CalibrationMaster(
                    id=UUID(row["id"]),
                    workspace_id=UUID(row["workspace_id"]),
                    kind=row["kind"],
                    version_num=row["version_num"],
                    artifact_id=UUID(row["artifact_id"]) if row["artifact_id"] else None,
                    parameters=_loads(row["parameters"], {}),
                    notes=row["notes"] or "",
                    created_at=row["created_at"],
                )
            )
        return out

    def save_analysis_product(self, product: AnalysisProduct) -> AnalysisProduct:
        now = utc_now_iso()
        self._conn.execute(
            """
            INSERT INTO analysis_products(
                id, workspace_id, program_id, product_type, version_num, parent_product_id,
                is_publishable, parameters, summary, state, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(product.id),
                str(product.workspace_id),
                str(product.program_id) if product.program_id else None,
                product.product_type,
                product.version_num,
                str(product.parent_product_id) if product.parent_product_id else None,
                1 if product.is_publishable else 0,
                _j(product.parameters),
                _j(product.summary),
                product.state,
                now,
                now,
            ),
        )
        self._conn.commit()
        return product

    def get_analysis_product(self, product_id: UUID) -> AnalysisProduct | None:
        row = self._conn.execute(
            "SELECT * FROM analysis_products WHERE id = ? AND deleted_at IS NULL",
            (str(product_id),),
        ).fetchone()
        if row is None:
            return None
        return AnalysisProduct(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            program_id=UUID(row["program_id"]) if row["program_id"] else None,
            product_type=row["product_type"],
            version_num=row["version_num"],
            parent_product_id=UUID(row["parent_product_id"]) if row["parent_product_id"] else None,
            is_publishable=bool(row["is_publishable"]),
            parameters=_loads(row["parameters"], {}),
            summary=_loads(row["summary"], {}),
            state=row["state"],
        )

    def list_analysis_products(
        self,
        workspace_id: UUID,
        *,
        product_type: str | None = None,
        limit: int = 200,
    ) -> list[AnalysisProduct]:
        if product_type:
            rows = self._conn.execute(
                """
                SELECT * FROM analysis_products
                WHERE workspace_id = ? AND deleted_at IS NULL AND product_type = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (str(workspace_id), product_type, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT * FROM analysis_products
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (str(workspace_id), limit),
            ).fetchall()
        out: list[AnalysisProduct] = []
        for row in rows:
            out.append(
                AnalysisProduct(
                    id=UUID(row["id"]),
                    workspace_id=UUID(row["workspace_id"]),
                    program_id=UUID(row["program_id"]) if row["program_id"] else None,
                    product_type=row["product_type"],
                    version_num=row["version_num"],
                    parent_product_id=(
                        UUID(row["parent_product_id"]) if row["parent_product_id"] else None
                    ),
                    is_publishable=bool(row["is_publishable"]),
                    parameters=_loads(row["parameters"], {}),
                    summary=_loads(row["summary"], {}),
                    state=row["state"],
                )
            )
        return out

    def link_product_observation(self, product_id: UUID, observation_id: UUID) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO analysis_product_observations(product_id, observation_id)
            VALUES (?, ?)
            """,
            (str(product_id), str(observation_id)),
        )
        self._conn.commit()

    def save_measurement_points(
        self,
        product_id: UUID,
        points: list[dict],
    ) -> int:
        for i, pt in enumerate(points):
            self._conn.execute(
                """
                INSERT INTO measurement_points(
                    id, product_id, t_utc, sequence_index, x, y, y_err, band, meta
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(pt.get("id") or new_id_local()),
                    str(product_id),
                    pt.get("t_utc"),
                    pt.get("sequence_index", i),
                    float(pt["x"]),
                    float(pt["y"]),
                    pt.get("y_err"),
                    pt.get("band"),
                    _j(pt.get("meta") or {}),
                ),
            )
        self._conn.commit()
        return len(points)

    def list_measurement_points(self, product_id: UUID) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT * FROM measurement_points
            WHERE product_id = ?
            ORDER BY sequence_index, t_utc
            """,
            (str(product_id),),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_artifact_uri(self, artifact_id: UUID) -> str | None:
        row = self._conn.execute(
            "SELECT uri FROM artifacts WHERE id = ?", (str(artifact_id),)
        ).fetchone()
        return None if row is None else row["uri"]

    # --- network submissions (v5) ---
    def save_network_submission(self, sub: Any) -> Any:
        from astrocitizen.contribution.models import NetworkSubmission

        assert isinstance(sub, NetworkSubmission)
        now = utc_now_iso()
        existing = self.get_network_submission(sub.id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO network_submissions(
                    id, workspace_id, network, status, artifact_uri, product_id,
                    payload_summary, remote_ack, error, created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(sub.id),
                    str(sub.workspace_id),
                    sub.network,
                    sub.status,
                    sub.artifact_uri,
                    str(sub.product_id) if sub.product_id else None,
                    _j(sub.payload_summary),
                    sub.remote_ack,
                    sub.error,
                    now,
                    now,
                    sub.version,
                ),
            )
            sub.created_at = now
        else:
            self._conn.execute(
                """
                UPDATE network_submissions SET
                    status = ?, artifact_uri = ?, product_id = ?,
                    payload_summary = ?, remote_ack = ?, error = ?,
                    updated_at = ?, version = version + 1
                WHERE id = ? AND deleted_at IS NULL
                """,
                (
                    sub.status,
                    sub.artifact_uri,
                    str(sub.product_id) if sub.product_id else None,
                    _j(sub.payload_summary),
                    sub.remote_ack,
                    sub.error,
                    now,
                    str(sub.id),
                ),
            )
        sub.updated_at = now
        self._conn.commit()
        return sub

    def get_network_submission(self, submission_id: UUID) -> Any | None:
        from astrocitizen.contribution.models import NetworkSubmission

        row = self._conn.execute(
            "SELECT * FROM network_submissions WHERE id = ? AND deleted_at IS NULL",
            (str(submission_id),),
        ).fetchone()
        if row is None:
            return None
        return NetworkSubmission(
            id=UUID(row["id"]),
            workspace_id=UUID(row["workspace_id"]),
            network=row["network"],
            status=row["status"],
            artifact_uri=row["artifact_uri"],
            product_id=UUID(row["product_id"]) if row["product_id"] else None,
            payload_summary=_loads(row["payload_summary"], {}),
            remote_ack=row["remote_ack"],
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=int(row["version"]),
        )

    def list_network_submissions(
        self, workspace_id: UUID, *, network: str | None = None
    ) -> list[Any]:
        if network:
            rows = self._conn.execute(
                """
                SELECT id FROM network_submissions
                WHERE workspace_id = ? AND network = ? AND deleted_at IS NULL
                ORDER BY created_at DESC
                """,
                (str(workspace_id), network),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """
                SELECT id FROM network_submissions
                WHERE workspace_id = ? AND deleted_at IS NULL
                ORDER BY created_at DESC
                """,
                (str(workspace_id),),
            ).fetchall()
        out = []
        for r in rows:
            item = self.get_network_submission(UUID(r["id"]))
            if item is not None:
                out.append(item)
        return out

    # --- knowledge corpus (v6 / AC-191) ---
    def upsert_knowledge_document(self, doc: Any) -> Any:
        from astrocitizen.knowledge.models import KnowledgeDocument

        assert isinstance(doc, KnowledgeDocument)
        now = utc_now_iso()
        doc_id = (doc.id or doc.source_id).strip()
        source_id = (doc.source_id or doc_id).strip()
        if not doc_id or not source_id:
            raise ValueError("knowledge document exige id/source_id")
        existing = self._get_knowledge_document_any(doc_id)
        if existing is None and source_id != doc_id:
            existing = self._get_knowledge_document_any(source_id)
        if existing is None:
            self._conn.execute(
                """
                INSERT INTO knowledge_documents(
                    id, source_id, path, title, trust_tier, license_id, lang,
                    topics, networks, content_hash, corpus_version, status,
                    created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc_id,
                    source_id,
                    doc.path,
                    doc.title,
                    doc.trust_tier,
                    doc.license_id,
                    doc.lang,
                    _j(list(doc.topics or [])),
                    _j(list(doc.networks or [])),
                    doc.content_hash,
                    doc.corpus_version,
                    doc.status or "planned",
                    now,
                    now,
                    doc.version,
                ),
            )
            doc.id = doc_id
            doc.source_id = source_id
            doc.created_at = now
        else:
            self._conn.execute(
                """
                UPDATE knowledge_documents SET
                    source_id = ?, path = ?, title = ?, trust_tier = ?,
                    license_id = ?, lang = ?, topics = ?, networks = ?,
                    content_hash = ?, corpus_version = ?, status = ?,
                    deleted_at = NULL, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (
                    source_id,
                    doc.path,
                    doc.title,
                    doc.trust_tier,
                    doc.license_id,
                    doc.lang,
                    _j(list(doc.topics or [])),
                    _j(list(doc.networks or [])),
                    doc.content_hash,
                    doc.corpus_version,
                    doc.status or "planned",
                    now,
                    existing.id,
                ),
            )
            doc.id = existing.id
            doc.source_id = source_id
            doc.created_at = existing.created_at
            doc.version = int(existing.version) + 1
        doc.updated_at = now
        self._conn.commit()
        return doc

    def get_knowledge_document(self, document_id: str) -> Any | None:
        from astrocitizen.knowledge.models import KnowledgeDocument

        key = (document_id or "").strip()
        if not key:
            return None
        row = self._conn.execute(
            """
            SELECT * FROM knowledge_documents
            WHERE (id = ? OR source_id = ?) AND deleted_at IS NULL
            """,
            (key, key),
        ).fetchone()
        if row is None:
            return None
        return KnowledgeDocument(
            id=row["id"],
            source_id=row["source_id"],
            path=row["path"],
            title=row["title"],
            trust_tier=row["trust_tier"],
            license_id=row["license_id"],
            lang=row["lang"],
            topics=list(_loads(row["topics"], [])),
            networks=list(_loads(row["networks"], [])),
            content_hash=row["content_hash"],
            corpus_version=row["corpus_version"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=int(row["version"]),
        )

    def _get_knowledge_document_any(self, document_id: str) -> Any | None:
        """Inclui soft-deleted (para re-ingest)."""
        from astrocitizen.knowledge.models import KnowledgeDocument

        key = (document_id or "").strip()
        if not key:
            return None
        row = self._conn.execute(
            "SELECT * FROM knowledge_documents WHERE id = ? OR source_id = ?",
            (key, key),
        ).fetchone()
        if row is None:
            return None
        return KnowledgeDocument(
            id=row["id"],
            source_id=row["source_id"],
            path=row["path"],
            title=row["title"],
            trust_tier=row["trust_tier"],
            license_id=row["license_id"],
            lang=row["lang"],
            topics=list(_loads(row["topics"], [])),
            networks=list(_loads(row["networks"], [])),
            content_hash=row["content_hash"],
            corpus_version=row["corpus_version"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=int(row["version"]),
        )

    def list_knowledge_documents(
        self,
        *,
        trust_tier: str | None = None,
        status: str | None = None,
        lang: str | None = None,
    ) -> list[Any]:
        clauses = ["deleted_at IS NULL"]
        params: list[Any] = []
        if trust_tier:
            clauses.append("trust_tier = ?")
            params.append(trust_tier)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if lang:
            clauses.append("lang = ?")
            params.append(lang)
        where = " AND ".join(clauses)
        rows = self._conn.execute(
            f"""
            SELECT id FROM knowledge_documents
            WHERE {where}
            ORDER BY source_id ASC
            """,
            params,
        ).fetchall()
        out = []
        for r in rows:
            item = self.get_knowledge_document(r["id"])
            if item is not None:
                out.append(item)
        return out

    def soft_delete_knowledge_document(self, document_id: str) -> None:
        now = utc_now_iso()
        key = (document_id or "").strip()
        doc = self.get_knowledge_document(key)
        if doc is None:
            raise NotFoundError(f"knowledge_documents nao encontrado: {document_id}")
        self._conn.execute(
            """
            UPDATE knowledge_chunks SET deleted_at = ?, updated_at = ?, version = version + 1
            WHERE document_id = ? AND deleted_at IS NULL
            """,
            (now, now, doc.id),
        )
        cur = self._conn.execute(
            """
            UPDATE knowledge_documents SET deleted_at = ?, updated_at = ?, version = version + 1
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, doc.id),
        )
        if cur.rowcount == 0:
            raise NotFoundError(f"knowledge_documents nao encontrado: {document_id}")
        self._conn.commit()

    def upsert_knowledge_chunk(self, chunk: Any) -> Any:
        from astrocitizen.knowledge.models import KnowledgeChunk

        assert isinstance(chunk, KnowledgeChunk)
        now = utc_now_iso()
        chunk_id = (chunk.id or "").strip()
        if not chunk_id:
            raise ValueError("knowledge chunk exige id")
        if not (chunk.chunk_hash or "").strip():
            raise ValueError("knowledge chunk exige chunk_hash")
        doc = self.get_knowledge_document(chunk.document_id or chunk.source_id)
        if doc is None:
            raise NotFoundError(
                f"documento KB nao encontrado para chunk: {chunk.document_id}"
            )
        existing_row = self._conn.execute(
            "SELECT * FROM knowledge_chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        source_id = (chunk.source_id or doc.source_id).strip()
        trust = (chunk.trust_tier or doc.trust_tier).strip()
        if existing_row is None:
            self._conn.execute(
                """
                INSERT INTO knowledge_chunks(
                    id, document_id, source_id, path, title, trust_tier, lang,
                    topics, po_id, network, pipeline_stage, token_estimate,
                    chunk_hash, corpus_version, body, sort_order,
                    created_at, updated_at, version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    doc.id,
                    source_id,
                    chunk.path,
                    chunk.title,
                    trust,
                    chunk.lang,
                    _j(list(chunk.topics or [])),
                    chunk.po_id,
                    chunk.network,
                    chunk.pipeline_stage,
                    chunk.token_estimate,
                    chunk.chunk_hash,
                    chunk.corpus_version,
                    chunk.body,
                    int(chunk.sort_order or 0),
                    now,
                    now,
                    chunk.version,
                ),
            )
            chunk.created_at = now
        else:
            self._conn.execute(
                """
                UPDATE knowledge_chunks SET
                    document_id = ?, source_id = ?, path = ?, title = ?,
                    trust_tier = ?, lang = ?, topics = ?, po_id = ?, network = ?,
                    pipeline_stage = ?, token_estimate = ?, chunk_hash = ?,
                    corpus_version = ?, body = ?, sort_order = ?,
                    deleted_at = NULL, updated_at = ?, version = version + 1
                WHERE id = ?
                """,
                (
                    doc.id,
                    source_id,
                    chunk.path,
                    chunk.title,
                    trust,
                    chunk.lang,
                    _j(list(chunk.topics or [])),
                    chunk.po_id,
                    chunk.network,
                    chunk.pipeline_stage,
                    chunk.token_estimate,
                    chunk.chunk_hash,
                    chunk.corpus_version,
                    chunk.body,
                    int(chunk.sort_order or 0),
                    now,
                    chunk_id,
                ),
            )
            chunk.created_at = existing_row["created_at"]
            chunk.version = int(existing_row["version"]) + 1
        chunk.id = chunk_id
        chunk.document_id = doc.id
        chunk.source_id = source_id
        chunk.trust_tier = trust
        chunk.updated_at = now
        self._conn.commit()
        return chunk

    def get_knowledge_chunk(self, chunk_id: str) -> Any | None:
        from astrocitizen.knowledge.models import KnowledgeChunk

        key = (chunk_id or "").strip()
        if not key:
            return None
        row = self._conn.execute(
            "SELECT * FROM knowledge_chunks WHERE id = ? AND deleted_at IS NULL",
            (key,),
        ).fetchone()
        if row is None:
            return None
        return KnowledgeChunk(
            id=row["id"],
            document_id=row["document_id"],
            source_id=row["source_id"],
            body=row["body"],
            trust_tier=row["trust_tier"],
            chunk_hash=row["chunk_hash"],
            path=row["path"],
            title=row["title"],
            lang=row["lang"],
            topics=list(_loads(row["topics"], [])),
            po_id=row["po_id"],
            network=row["network"],
            pipeline_stage=row["pipeline_stage"],
            token_estimate=row["token_estimate"],
            corpus_version=row["corpus_version"],
            sort_order=int(row["sort_order"] or 0),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            version=int(row["version"]),
        )

    def list_knowledge_chunks(
        self,
        *,
        source_id: str | None = None,
        document_id: str | None = None,
        trust_tier: str | None = None,
    ) -> list[Any]:
        clauses = ["deleted_at IS NULL"]
        params: list[Any] = []
        if source_id:
            clauses.append("source_id = ?")
            params.append(source_id)
        if document_id:
            clauses.append("document_id = ?")
            params.append(document_id)
        if trust_tier:
            clauses.append("trust_tier = ?")
            params.append(trust_tier)
        where = " AND ".join(clauses)
        rows = self._conn.execute(
            f"""
            SELECT id FROM knowledge_chunks
            WHERE {where}
            ORDER BY document_id ASC, sort_order ASC, id ASC
            """,
            params,
        ).fetchall()
        out = []
        for r in rows:
            item = self.get_knowledge_chunk(r["id"])
            if item is not None:
                out.append(item)
        return out

    def soft_delete_knowledge_chunk(self, chunk_id: str) -> None:
        now = utc_now_iso()
        key = (chunk_id or "").strip()
        cur = self._conn.execute(
            """
            UPDATE knowledge_chunks SET deleted_at = ?, updated_at = ?, version = version + 1
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, key),
        )
        if cur.rowcount == 0:
            raise NotFoundError(f"knowledge_chunks nao encontrado: {chunk_id}")
        self._conn.commit()
