"""CLI do AstroCitizen (S1+S2: init-db, site, equipment, program, target, plan)."""

from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from astrocitizen import __version__
from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.hardware import create_camera
from astrocitizen.adapters.meteo import ManualMeteo, OpenMeteo, RainViewerRadar
from astrocitizen.adapters.sky import AstropyEphemeris, SimbadResolver
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis import AperturePhotometry
from astrocitizen.contribution.aavso import ExportAavso
from astrocitizen.desktop import run_gui
from astrocitizen.inventory.models import Equipment, Site
from astrocitizen.observatory import CaptureObservation, ExecuteSession
from astrocitizen.planning import EditDailyPlan, GenerateDailyPlan, Target
from astrocitizen.planning.meteo_rules import evaluate_meteo_window
from astrocitizen.programs.models import Program
from astrocitizen.programs.seed import seed_program_templates
from astrocitizen.programs.workflows import P1_WORKFLOWS, workflow_for
from astrocitizen.reduction import ApplyCalibration, BuildMaster, fits_stats
from astrocitizen.shared import CONTEXT_MODULES
from astrocitizen.shared.ids import new_id
from astrocitizen.shared.paths import default_artifacts_root, default_db_path
from astrocitizen.workspace.models import Workspace

DEFAULT_WORKSPACE_NAME = "default"


def _open_archive(db: Path) -> SqliteArchive:
    archive = SqliteArchive(db)
    archive.migrate()
    return archive


def _ensure_default_workspace(archive: SqliteArchive) -> Workspace:
    workspaces = archive.list_workspaces()
    if workspaces:
        return workspaces[0]
    ws = Workspace(id=new_id(), name=DEFAULT_WORKSPACE_NAME)
    return archive.upsert_workspace(ws)


def _resolve_site(archive: SqliteArchive, ws: Workspace, site_arg: str | None) -> Site:
    sites = archive.list_sites(ws.id)
    if not sites:
        raise SystemExit("nenhum site; use: astrocitizen site add ...")
    if site_arg:
        sid = UUID(site_arg)
        site = archive.get_site(sid)
        if site is None:
            raise SystemExit(f"site nao encontrado: {site_arg}")
        return site
    for s in sites:
        if s.is_default:
            return s
    return sites[0]


def _cmd_init_db(args: argparse.Namespace) -> int:
    db = Path(args.db)
    artifacts = Path(args.artifacts)
    archive = _open_archive(db)
    ws = _ensure_default_workspace(archive)
    n = seed_program_templates(archive)
    LocalArtifactStore(artifacts)
    print(f"db={db}")
    print(f"artifacts={artifacts.resolve()}")
    print(f"schema={archive.migrate()} workspace={ws.id} name={ws.name}")
    print(f"templates_seeded={n}")
    archive.close()
    return 0


def _cmd_site_add(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site = Site(
        id=new_id(),
        workspace_id=ws.id,
        name=args.name,
        latitude_deg=args.lat,
        longitude_deg=args.lon,
        elevation_m=args.elev,
        timezone=args.tz,
        is_default=args.default,
    )
    archive.upsert_site(site)
    print(f"{site.id}\t{site.name}\t{site.latitude_deg},{site.longitude_deg}")
    archive.close()
    return 0


def _cmd_site_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for s in archive.list_sites(ws.id):
        flag = "*" if s.is_default else " "
        print(f"{flag}\t{s.id}\t{s.name}\t{s.latitude_deg},{s.longitude_deg}\t{s.timezone}")
    archive.close()
    return 0


def _cmd_equipment_add(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    eq = Equipment(
        id=new_id(),
        workspace_id=ws.id,
        type=args.type,
        name=args.name,
        backend=args.backend,
    )
    archive.upsert_equipment(eq)
    print(f"{eq.id}\t{eq.type}\t{eq.name}\t{eq.backend or '-'}")
    archive.close()
    return 0


def _cmd_equipment_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for eq in archive.list_equipment(ws.id):
        print(f"{eq.id}\t{eq.type}\t{eq.name}\t{eq.backend or '-'}")
    archive.close()
    return 0


def _cmd_program_templates(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    if not archive.list_program_templates():
        seed_program_templates(archive)
    for t in archive.list_program_templates(class_=args.class_):
        nets = ",".join(t.default_networks) if t.default_networks else "-"
        print(f"{t.id}\t{t.priority}\t{t.name}\t{nets}")
    archive.close()
    return 0


def _cmd_program_create(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    if not archive.list_program_templates():
        seed_program_templates(archive)
    tmpl = archive.get_program_template(args.template)
    if tmpl is None:
        print(f"template nao encontrado: {args.template}")
        archive.close()
        return 1
    name = args.name or tmpl.name
    program = Program(
        id=new_id(),
        workspace_id=ws.id,
        template_id=tmpl.id,
        name=name,
        state="active" if args.active else "draft",
        priority=args.priority,
        export_networks=list(tmpl.default_networks),
        minimum_product=tmpl.minimum_product,
    )
    archive.upsert_program(program)
    print(f"{program.id}\t{program.template_id}\t{program.state}\t{program.name}")
    archive.close()
    return 0


def _cmd_program_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for p in archive.list_programs(ws.id, state=args.state):
        print(f"{p.id}\t{p.template_id}\t{p.state}\tp={p.priority}\t{p.name}")
    archive.close()
    return 0


def _cmd_program_activate(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    program = archive.get_program(UUID(args.id))
    if program is None:
        print(f"programa nao encontrado: {args.id}")
        archive.close()
        return 1
    program.state = "active"
    archive.upsert_program(program)
    print(f"{program.id}\tactive\t{program.name}")
    archive.close()
    return 0


def _cmd_program_link_target(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    archive.link_program_target(
        UUID(args.program),
        UUID(args.target),
        role=args.role,
        sort_order=args.sort,
    )
    print(f"linked program={args.program} target={args.target} role={args.role}")
    archive.close()
    return 0


def _cmd_target_add(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    ra, dec = args.ra, args.dec
    external_ids: dict = {}
    if (ra is None or dec is None) and args.resolve:
        resolved = SimbadResolver().resolve(args.name)
        ra = resolved["ra_deg"]
        dec = resolved["dec_deg"]
        external_ids = dict(resolved.get("external_ids") or {})
    if ra is None or dec is None:
        print("indique --ra/--dec ou --resolve (requer astroquery)")
        archive.close()
        return 1
    target = Target(
        id=new_id(),
        workspace_id=ws.id,
        designation=args.name,
        ra_deg=ra,
        dec_deg=dec,
        target_type=args.type,
        external_ids=external_ids,
    )
    archive.upsert_target(target)
    print(f"{target.id}\t{target.designation}\t{target.ra_deg},{target.dec_deg}")
    archive.close()
    return 0


def _cmd_target_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for t in archive.list_targets(ws.id):
        print(f"{t.id}\t{t.designation}\t{t.ra_deg},{t.dec_deg}\t{t.target_type}")
    archive.close()
    return 0


def _cmd_plan_generate(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site = _resolve_site(archive, ws, args.site)
    if args.meteo == "api":
        meteo = OpenMeteo()
    else:
        meteo = ManualMeteo(
            cloud_cover_pct=args.cloud,
            wind_ms=args.wind,
            humidity_pct=args.humidity,
            precipitation=args.precip,
        )
    plan = GenerateDailyPlan(archive, AstropyEphemeris(), meteo).execute(
        workspace_id=ws.id,
        site_id=site.id,
        night_date=args.date,
    )
    blocks = archive.list_observation_blocks(plan.id)
    print(f"plan={plan.id}\tnight={plan.night_date}\tsite={site.name}\tblocks={len(blocks)}")
    for b in blocks:
        reason = b.status_reason or "-"
        print(f"  {b.sort_order}\t{b.status}\tpri={b.priority}\t{b.id}\t{reason}")
    archive.close()
    return 0


def _cmd_plan_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site_id = UUID(args.site) if args.site else None
    for p in archive.list_daily_plans(ws.id, site_id=site_id):
        print(f"{p.id}\t{p.night_date}\t{p.state}\tsite={p.site_id}")
    archive.close()
    return 0


def _cmd_plan_show(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    plan = archive.get_daily_plan(UUID(args.id))
    if plan is None:
        print(f"plano nao encontrado: {args.id}")
        archive.close()
        return 1
    print(f"plan={plan.id}\tnight={plan.night_date}\tstate={plan.state}\tv={plan.version}")
    for b in archive.list_observation_blocks(plan.id):
        reason = b.status_reason or "-"
        print(
            f"  {b.sort_order}\t{b.status}\tpri={b.priority}\t"
            f"alt={b.predicted_altitude_deg}\t{b.id}\t{reason}"
        )
    archive.close()
    return 0


def _cmd_plan_edit(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    editor = EditDailyPlan(archive)
    if args.reorder:
        ids = [UUID(x) for x in args.reorder.split(",")]
        editor.reorder(UUID(args.plan), ids)
        print("reordered")
    elif args.block:
        editor.set_block_status(
            UUID(args.block),
            args.status,
            reason=args.reason,
            notes=args.notes,
        )
        print(f"updated block={args.block} status={args.status}")
    else:
        print("use --block ... --status ... ou --reorder id1,id2,...")
        archive.close()
        return 1
    archive.close()
    return 0


def _cmd_session_start(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    session = ExecuteSession(archive).start(
        workspace_id=ws.id,
        plan_id=UUID(args.plan),
    )
    print(f"session={session.id}\tplan={session.daily_plan_id}\tv={session.daily_plan_version}")
    archive.close()
    return 0


def _cmd_session_capture(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    artifacts = LocalArtifactStore(Path(args.artifacts))
    camera = create_camera(args.backend)
    camera.connect()
    obs = CaptureObservation(archive, camera, artifacts).execute(
        session_id=UUID(args.session),
        block_id=UUID(args.block) if args.block else None,
        exptime_s=args.exptime,
        frame_type=args.frame,
    )
    print(f"observation={obs.id}\tsimulated={obs.simulated}\tbackend={obs.camera_backend}")
    archive.close()
    return 0


def _cmd_session_end(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    session = ExecuteSession(archive).end(UUID(args.session), abort=args.abort)
    print(f"session={session.id}\tstate={session.state}")
    archive.close()
    return 0


def _cmd_session_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for s in archive.list_sessions(ws.id, state=args.state):
        print(f"{s.id}\t{s.state}\tplan={s.daily_plan_id}\t{s.started_at_utc}")
    archive.close()
    return 0


def _cmd_gui(args: argparse.Namespace) -> int:
    return run_gui(args.db)


def _cmd_reduce_master(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    paths = [Path(x) for x in args.fits]
    master = BuildMaster(archive, store).execute(
        workspace_id=ws.id, kind=args.kind, fits_paths=paths, notes=args.notes or ""
    )
    print(f"master={master.id}\tkind={master.kind}\tv={master.version_num}")
    archive.close()
    return 0


def _cmd_reduce_apply(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = ApplyCalibration(archive, store).execute(
        workspace_id=ws.id,
        light_uri=args.light,
        dark_master_id=UUID(args.dark) if args.dark else None,
        flat_master_id=UUID(args.flat) if args.flat else None,
        bias_master_id=UUID(args.bias) if args.bias else None,
        observation_id=UUID(args.observation) if args.observation else None,
    )
    print(f"product={product.id}\ttype={product.product_type}\tmean={product.summary.get('mean')}")
    archive.close()
    return 0


def _cmd_reduce_stats(args: argparse.Namespace) -> int:
    st = fits_stats(Path(args.fits))
    for k, v in st.items():
        if k == "header_keys":
            continue
        print(f"{k}={v}")
    return 0


def _cmd_reduce_masters_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    for m in archive.list_calibration_masters(ws.id, kind=args.kind):
        print(f"{m.id}\t{m.kind}\tv{m.version_num}\tart={m.artifact_id}")
    archive.close()
    return 0


def _cmd_analyze_photometry(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    comp = None
    if args.comp is not None:
        cx, cy = args.comp.split(",")
        comp = (float(cx), float(cy))
    product = AperturePhotometry(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        x=args.x,
        y=args.y,
        band=args.band,
        comp_xy=comp,
        program_id=UUID(args.program) if args.program else None,
    )
    print(
        f"product={product.id}\tmag={product.summary.get('mag')}\t"
        f"dmag={product.summary.get('dmag')}\tflux={product.summary.get('flux')}"
    )
    archive.close()
    return 0


def _cmd_analyze_export_aavso(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    out = ExportAavso(archive).execute(
        product_id=UUID(args.product),
        star_name=args.star,
        observer_code=args.obscode,
        out_path=Path(args.out),
        band=args.band,
    )
    print(f"wrote={out}")
    archive.close()
    return 0


def _cmd_workflow_list(args: argparse.Namespace) -> int:
    for tid, wf in P1_WORKFLOWS.items():
        print(f"{tid}\t{wf['analysis']}\t{wf['name']}")
        if args.verbose:
            print(f"  steps={','.join(wf['steps'])}")
    return 0


def _cmd_workflow_show(args: argparse.Namespace) -> int:
    wf = workflow_for(args.template)
    if wf is None:
        print(f"sem workflow P1 para {args.template}")
        return 1
    print(f"{args.template}\t{wf['name']}")
    for s in wf["steps"]:
        print(f"  - {s}")
    print(f"networks={','.join(wf.get('networks') or []) or '-'}")
    return 0



def _cmd_meteo_forecast(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site = _resolve_site(archive, ws, args.site)
    eph = AstropyEphemeris()
    night = eph.night_window(
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        elevation_m=site.elevation_m,
        night_date=args.date,
        night_start_rule=site.night_start_rule,
    )
    if args.provider == "manual":
        meteo = ManualMeteo(
            cloud_cover_pct=args.cloud,
            wind_ms=args.wind,
            humidity_pct=args.humidity,
            precipitation=args.precip,
        )
    else:
        meteo = OpenMeteo()
    fc = meteo.forecast(
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        start_utc=night["start_utc"],
        end_utc=night["end_utc"],
    )
    ok, reason = evaluate_meteo_window(fc, site.meteo_thresholds)
    print(f"site={site.name}\tnight={args.date}\twindow={night['start_utc']}..{night['end_utc']}")
    print(
        f"ok={ok}\tcloud_max={fc.get('cloud_cover_pct')}\twind_max={fc.get('wind_ms')}\t"
        f"rh_max={fc.get('humidity_pct')}\tdew_margin_min={fc.get('dew_margin_c')}\t"
        f"precip={fc.get('precipitation')}\tprob_max={fc.get('precip_probability_pct')}"
    )
    if reason:
        print(f"reason={reason}")
    hours = fc.get("hourly") or []
    print(f"hours={len(hours)}")
    if args.verbose:
        for h in hours:
            print(
                f"  {h.get('time_utc')}\tcloud={h.get('cloud_cover_pct')}\t"
                f"wind={h.get('wind_ms')}\trh={h.get('humidity_pct')}\t"
                f"dew={h.get('dewpoint_c')}\tprecip_mm={h.get('precipitation_mm')}\t"
                f"prob={h.get('precip_probability_pct')}"
            )
    archive.close()
    return 0 if ok else 2


def _cmd_meteo_radar(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site = _resolve_site(archive, ws, args.site)
    store = LocalArtifactStore(Path(args.artifacts))
    out = store.root / "radar" / f"{site.id}_{args.zoom}.png"
    meta = RainViewerRadar().region_image(
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        zoom=args.zoom,
        size=args.size,
        out_path=out,
    )
    img = Path(meta["image_path"])
    uri = store.put(img, key=f"radar/{site.id}/{img.name}")
    print(f"site={site.name}\tlat={site.latitude_deg}\tlon={site.longitude_deg}")
    print(f"path={meta['image_path']}\turi={uri}\tbytes={meta['bytes']}")
    print(f"radar_time={meta['radar_time']}\t{meta['attribution']}")
    archive.close()
    return 0



def _add_db_arg(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--db",
        default=str(default_db_path()),
        help="Caminho do SQLite (default: ~/.astrocitizen/astrocitizen.sqlite3)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="astrocitizen",
        description="AstroCitizen - plataforma de astronomia observacional cidada",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"astrocitizen {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("version", help="Mostrar versao do pacote")
    sub.add_parser("modules", help="Listar bounded contexts do skeleton")

    p_init = sub.add_parser("init-db", help="Criar BD SQLite, workspace e seed PO-*")
    _add_db_arg(p_init)
    p_init.add_argument(
        "--artifacts",
        default=str(default_artifacts_root()),
        help="Root do ArtifactStore local",
    )
    p_init.set_defaults(func=_cmd_init_db)

    p_site = sub.add_parser("site", help="Gerir sites observacionais")
    site_sub = p_site.add_subparsers(dest="site_cmd", required=True)
    p_site_add = site_sub.add_parser("add", help="Adicionar site")
    _add_db_arg(p_site_add)
    p_site_add.add_argument("--name", required=True)
    p_site_add.add_argument("--lat", type=float, required=True)
    p_site_add.add_argument("--lon", type=float, required=True)
    p_site_add.add_argument("--elev", type=float, default=0.0)
    p_site_add.add_argument("--tz", default="UTC")
    p_site_add.add_argument("--default", action="store_true")
    p_site_add.set_defaults(func=_cmd_site_add)
    p_site_list = site_sub.add_parser("list", help="Listar sites")
    _add_db_arg(p_site_list)
    p_site_list.set_defaults(func=_cmd_site_list)

    p_eq = sub.add_parser("equipment", help="Gerir inventario de equipamento")
    eq_sub = p_eq.add_subparsers(dest="eq_cmd", required=True)
    p_eq_add = eq_sub.add_parser("add", help="Adicionar equipamento")
    _add_db_arg(p_eq_add)
    p_eq_add.add_argument("--type", required=True, help="camera|mount|focuser|filter_wheel|...")
    p_eq_add.add_argument("--name", required=True)
    p_eq_add.add_argument("--backend", default=None)
    p_eq_add.set_defaults(func=_cmd_equipment_add)
    p_eq_list = eq_sub.add_parser("list", help="Listar equipamento")
    _add_db_arg(p_eq_list)
    p_eq_list.set_defaults(func=_cmd_equipment_list)

    p_prog = sub.add_parser("program", help="Gerir programas observacionais")
    prog_sub = p_prog.add_subparsers(dest="prog_cmd", required=True)
    p_tmpl = prog_sub.add_parser("templates", help="Listar templates PO-*")
    _add_db_arg(p_tmpl)
    p_tmpl.add_argument("--class", dest="class_", default=None, help="Filtrar por classe A-K")
    p_tmpl.set_defaults(func=_cmd_program_templates)
    p_create = prog_sub.add_parser("create", help="Criar programa a partir de template")
    _add_db_arg(p_create)
    p_create.add_argument("--template", required=True, help="ex.: PO-A01")
    p_create.add_argument("--name", default=None)
    p_create.add_argument("--active", action="store_true")
    p_create.add_argument("--priority", type=int, default=10)
    p_create.set_defaults(func=_cmd_program_create)
    p_plist = prog_sub.add_parser("list", help="Listar programas")
    _add_db_arg(p_plist)
    p_plist.add_argument("--state", default=None)
    p_plist.set_defaults(func=_cmd_program_list)
    p_act = prog_sub.add_parser("activate", help="Activar programa")
    _add_db_arg(p_act)
    p_act.add_argument("--id", required=True)
    p_act.set_defaults(func=_cmd_program_activate)
    p_link = prog_sub.add_parser("link-target", help="Associar alvo a programa")
    _add_db_arg(p_link)
    p_link.add_argument("--program", required=True)
    p_link.add_argument("--target", required=True)
    p_link.add_argument("--role", default="primary")
    p_link.add_argument("--sort", type=int, default=0)
    p_link.set_defaults(func=_cmd_program_link_target)

    p_tgt = sub.add_parser("target", help="Gerir alvos")
    tgt_sub = p_tgt.add_subparsers(dest="tgt_cmd", required=True)
    p_tadd = tgt_sub.add_parser("add", help="Adicionar alvo")
    _add_db_arg(p_tadd)
    p_tadd.add_argument("--name", required=True)
    p_tadd.add_argument("--ra", type=float, default=None)
    p_tadd.add_argument("--dec", type=float, default=None)
    p_tadd.add_argument("--type", default="star")
    p_tadd.add_argument("--resolve", action="store_true", help="Resolver via SIMBAD")
    p_tadd.set_defaults(func=_cmd_target_add)
    p_tlist = tgt_sub.add_parser("list", help="Listar alvos")
    _add_db_arg(p_tlist)
    p_tlist.set_defaults(func=_cmd_target_list)

    p_plan = sub.add_parser("plan", help="Programa diario")
    plan_sub = p_plan.add_subparsers(dest="plan_cmd", required=True)
    p_gen = plan_sub.add_parser("generate", help="Gerar/regenerar plano draft")
    _add_db_arg(p_gen)
    p_gen.add_argument("--date", required=True, help="YYYY-MM-DD (noite civil)")
    p_gen.add_argument("--site", default=None, help="UUID do site (default: site *)")
    p_gen.add_argument("--meteo", choices=("manual", "api"), default="manual")
    p_gen.add_argument("--cloud", type=float, default=10.0)
    p_gen.add_argument("--wind", type=float, default=2.0)
    p_gen.add_argument("--humidity", type=float, default=40.0)
    p_gen.add_argument("--precip", action="store_true")
    p_gen.set_defaults(func=_cmd_plan_generate)
    p_pl = plan_sub.add_parser("list", help="Listar planos")
    _add_db_arg(p_pl)
    p_pl.add_argument("--site", default=None)
    p_pl.set_defaults(func=_cmd_plan_list)
    p_show = plan_sub.add_parser("show", help="Mostrar plano e blocos")
    _add_db_arg(p_show)
    p_show.add_argument("--id", required=True)
    p_show.set_defaults(func=_cmd_plan_show)
    p_edit = plan_sub.add_parser("edit", help="Editar blocos (RN-052)")
    _add_db_arg(p_edit)
    p_edit.add_argument("--plan", required=True)
    p_edit.add_argument("--block", default=None)
    p_edit.add_argument("--status", default="agendado")
    p_edit.add_argument("--reason", default=None)
    p_edit.add_argument("--notes", default=None)
    p_edit.add_argument("--reorder", default=None, help="ids separados por virgula")
    p_edit.set_defaults(func=_cmd_plan_edit)

    p_sess = sub.add_parser("session", help="Sessao observacional (S3)")
    sess_sub = p_sess.add_subparsers(dest="sess_cmd", required=True)
    p_ss = sess_sub.add_parser("start", help="Iniciar sessao (congela plano RN-056)")
    _add_db_arg(p_ss)
    p_ss.add_argument("--plan", required=True)
    p_ss.set_defaults(func=_cmd_session_start)
    p_sc = sess_sub.add_parser("capture", help="Expor e gravar FITS")
    _add_db_arg(p_sc)
    p_sc.add_argument("--session", required=True)
    p_sc.add_argument("--block", default=None)
    p_sc.add_argument("--exptime", type=float, default=1.0)
    p_sc.add_argument("--frame", default="light")
    p_sc.add_argument("--backend", default="sim", choices=("sim", "alpaca", "udrv"))
    p_sc.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_sc.set_defaults(func=_cmd_session_capture)
    p_se = sess_sub.add_parser("end", help="Terminar sessao")
    _add_db_arg(p_se)
    p_se.add_argument("--session", required=True)
    p_se.add_argument("--abort", action="store_true")
    p_se.set_defaults(func=_cmd_session_end)
    p_sl = sess_sub.add_parser("list", help="Listar sessoes")
    _add_db_arg(p_sl)
    p_sl.add_argument("--state", default=None)
    p_sl.set_defaults(func=_cmd_session_list)

    p_gui = sub.add_parser("gui", help="Abrir shell PySide6 (requer [gui])")
    _add_db_arg(p_gui)
    p_gui.set_defaults(func=_cmd_gui)

    p_red = sub.add_parser("reduce", help="Calibracao / masters / stats FITS")
    red_sub = p_red.add_subparsers(dest="red_cmd", required=True)
    p_rm = red_sub.add_parser("master", help="Construir master bias/dark/flat")
    _add_db_arg(p_rm)
    p_rm.add_argument("--kind", required=True, choices=("bias", "dark", "flat"))
    p_rm.add_argument("--fits", nargs="+", required=True)
    p_rm.add_argument("--notes", default="")
    p_rm.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_rm.set_defaults(func=_cmd_reduce_master)
    p_ra = red_sub.add_parser("apply", help="Aplicar calibracao a light")
    _add_db_arg(p_ra)
    p_ra.add_argument("--light", required=True, help="URI file:// do light")
    p_ra.add_argument("--bias", default=None)
    p_ra.add_argument("--dark", default=None)
    p_ra.add_argument("--flat", default=None)
    p_ra.add_argument("--observation", default=None)
    p_ra.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ra.set_defaults(func=_cmd_reduce_apply)
    p_rs = red_sub.add_parser("stats", help="Estatisticas FITS (viewer CLI)")
    p_rs.add_argument("--fits", required=True)
    p_rs.set_defaults(func=_cmd_reduce_stats)
    p_rl = red_sub.add_parser("masters", help="Listar masters")
    _add_db_arg(p_rl)
    p_rl.add_argument("--kind", default=None)
    p_rl.set_defaults(func=_cmd_reduce_masters_list)

    p_an = sub.add_parser("analyze", help="Analise (fotometria / export)")
    an_sub = p_an.add_subparsers(dest="an_cmd", required=True)
    p_ph = an_sub.add_parser("photometry", help="Fotometria de abertura")
    _add_db_arg(p_ph)
    p_ph.add_argument("--fits-uri", required=True)
    p_ph.add_argument("--x", type=float, required=True)
    p_ph.add_argument("--y", type=float, required=True)
    p_ph.add_argument("--band", default="V")
    p_ph.add_argument("--comp", default=None, help="x,y estrela comparacao")
    p_ph.add_argument("--program", default=None)
    p_ph.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ph.set_defaults(func=_cmd_analyze_photometry)
    p_ex = an_sub.add_parser("export-aavso", help="Export AAVSO Extended")
    _add_db_arg(p_ex)
    p_ex.add_argument("--product", required=True)
    p_ex.add_argument("--star", required=True)
    p_ex.add_argument("--obscode", required=True)
    p_ex.add_argument("--out", required=True)
    p_ex.add_argument("--band", default="V")
    p_ex.set_defaults(func=_cmd_analyze_export_aavso)

    p_wf = sub.add_parser("workflow", help="Workflows P1 (PO-J*, PO-A01)")
    wf_sub = p_wf.add_subparsers(dest="wf_cmd", required=True)
    p_wfl = wf_sub.add_parser("list", help="Listar workflows P1")
    p_wfl.add_argument("-v", "--verbose", action="store_true")
    p_wfl.set_defaults(func=_cmd_workflow_list)
    p_wfs = wf_sub.add_parser("show", help="Mostrar workflow de template")
    p_wfs.add_argument("--template", required=True)
    p_wfs.set_defaults(func=_cmd_workflow_show)


    p_meteo = sub.add_parser("meteo", help="Previsao horaria + radar de chuva")
    meteo_sub = p_meteo.add_subparsers(dest="meteo_cmd", required=True)
    p_mf = meteo_sub.add_parser("forecast", help="Open-Meteo hourly na janela da noite")
    _add_db_arg(p_mf)
    p_mf.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_mf.add_argument("--site", default=None)
    p_mf.add_argument("--provider", choices=("api", "manual"), default="api")
    p_mf.add_argument("--cloud", type=float, default=10.0)
    p_mf.add_argument("--wind", type=float, default=2.0)
    p_mf.add_argument("--humidity", type=float, default=40.0)
    p_mf.add_argument("--precip", action="store_true")
    p_mf.add_argument("-v", "--verbose", action="store_true")
    p_mf.set_defaults(func=_cmd_meteo_forecast)
    p_mr = meteo_sub.add_parser("radar", help="Imagem RainViewer centrada no Site")
    _add_db_arg(p_mr)
    p_mr.add_argument("--site", default=None)
    p_mr.add_argument("--zoom", type=int, default=6)
    p_mr.add_argument("--size", type=int, default=512, choices=(256, 512))
    p_mr.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_mr.set_defaults(func=_cmd_meteo_radar)


    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        print(__version__)
        return 0

    if args.command == "modules":
        for name in CONTEXT_MODULES:
            print(name)
        return 0

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return 1
    return int(func(args))


if __name__ == "__main__":
    raise SystemExit(main())
