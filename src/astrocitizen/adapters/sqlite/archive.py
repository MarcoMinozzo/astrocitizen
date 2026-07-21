"""SqliteArchive — implementacao SQLite do ArchivePort (S1)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID

from astrocitizen.adapters.sqlite.schema import SCHEMA_SQL, SCHEMA_VERSION
from astrocitizen.inventory.models import Equipment, InstrumentConfig, Site
from astrocitizen.programs.models import Program, ProgramTemplate
from astrocitizen.shared.errors import NotFoundError
from astrocitizen.shared.timeutil import utc_now_iso
from astrocitizen.workspace.models import Workspace


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
