"""CLI do AstroCitizen (S1+S2: init-db, site, equipment, program, target, plan)."""

from __future__ import annotations

import argparse
from pathlib import Path
from uuid import UUID

from astrocitizen import __version__
from astrocitizen.adapters.fs import LocalArtifactStore
from astrocitizen.adapters.hardware import create_camera
from astrocitizen.adapters.meteo import ManualMeteo, OpenMeteo, RainViewerRadar
from astrocitizen.adapters.platesolve import create_plate_solver
from astrocitizen.adapters.sky import AstropyEphemeris, SimbadResolver
from astrocitizen.adapters.sqlite import SqliteArchive
from astrocitizen.analysis import (
    AperturePhotometry,
    BlinkDiff,
    CalibrateWavelength,
    CountSunspots,
    ExtractSpectrum1D,
    InterpretSpectrum,
    MeasureAstrometry,
    PlateSolve,
)
from astrocitizen.contribution.aavso import ExportAavso
from astrocitizen.contribution.bess import annotate_existing_fits, write_bess_fits
from astrocitizen.contribution.credentials import LocalCredentialsStore
from astrocitizen.contribution.exoclock import ExportExoclock
from astrocitizen.contribution.iota import write_iota_pack
from astrocitizen.contribution.models import NetworkSubmission
from astrocitizen.contribution.mpc import MpcAdesSubmitter, write_ades_psv
from astrocitizen.contribution.solar import ExportSolarReport
from astrocitizen.contribution.tns import TnsClient, format_tns_at_report, write_tns_report
from astrocitizen.contribution.validate_minimum import validate_product_for_network
from astrocitizen.contribution.wds import ExportWds
from astrocitizen.contribution.cobs import ExportCobs
from astrocitizen.desktop import run_gui
from astrocitizen.inventory.models import Equipment, Site
from astrocitizen.observatory import (
    CaptureObservation,
    ExecuteSession,
    ImportEchelleOrders,
    ImportFits,
    ImportIotaPrediction,
    ImportPolarimetrySet,
    ImportRadioScan,
    ImportRadioSpectrum,
    ImportRadioTimeseries,
    ImportSpeckleCube,
    LogDoubleMeasure,
    LogVisualObservation,
    RegisterOccultationTiming,
)
from astrocitizen.observatory.import_fits import discover_fits_paths
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
    designation = args.name
    if (ra is None or dec is None) and getattr(args, "resolve_vsx", False):
        from astrocitizen.integrations.vsx import VsxProvider

        resolved = VsxProvider(archive=archive).search_object(args.name)
        ra = resolved["ra_deg"]
        dec = resolved["dec_deg"]
        external_ids = dict(resolved.get("external_ids") or {})
        designation = str(resolved.get("designation") or args.name)
    elif (ra is None or dec is None) and args.resolve:
        resolved = SimbadResolver().resolve(args.name)
        ra = resolved["ra_deg"]
        dec = resolved["dec_deg"]
        external_ids = dict(resolved.get("external_ids") or {})
    if ra is None or dec is None:
        print("indique --ra/--dec, --resolve (SIMBAD) ou --resolve-vsx")
        archive.close()
        return 1
    target = Target(
        id=new_id(),
        workspace_id=ws.id,
        designation=designation,
        ra_deg=ra,
        dec_deg=dec,
        target_type=args.type,
        external_ids=external_ids,
    )
    archive.upsert_target(target)
    extras = ""
    if external_ids.get("auid"):
        extras = f"\tauid={external_ids['auid']}"
    if external_ids.get("variability_type"):
        extras += f"\ttype={external_ids['variability_type']}"
    print(f"{target.id}\t{target.designation}\t{target.ra_deg},{target.dec_deg}{extras}")
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


def _cmd_import_fits(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    site = None
    if args.site:
        site = _resolve_site(archive, ws, args.site)
    program_id = UUID(args.program) if args.program else None
    target_id = UUID(args.target) if args.target else None
    paths = discover_fits_paths(Path(args.path), recursive=bool(args.recursive))
    if args.limit is not None:
        paths = paths[: max(int(args.limit), 0)]
    obs_list = ImportFits(archive, store).execute(
        workspace_id=ws.id,
        paths=paths,
        site_id=site.id if site else None,
        program_id=program_id,
        target_id=target_id,
        frame_type=args.frame_type,
        simulated=bool(args.simulated),
        notes=args.notes or "",
    )
    for obs in obs_list:
        obj = obs.headers_summary.get("OBJECT") or obs.headers_summary.get("OBJNAME") or "-"
        print(
            f"obs={obs.id}\twhen={obs.observed_at_utc}\tobject={obj}\t"
            f"state={obs.state}\tsim={obs.simulated}"
        )
    print(f"imported={len(obs_list)}")
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


def _cmd_analyze_spectrum(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    auto = bool(args.auto_trace or args.trace_y is None)
    if not auto and args.trace_y is None:
        print("indique --trace-y ou --auto-trace")
        archive.close()
        return 2
    product = ExtractSpectrum1D(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        trace_y=None if auto else float(args.trace_y),
        half_width=args.half_width,
        axis=args.axis,
        auto_trace=auto,
        subtract_sky=not bool(args.no_sky),
        sky_offset=args.sky_offset,
        sky_half_width=args.sky_width,
        wave0_nm=args.wave0,
        wave1_nm=args.wave1,
        pix_a=args.pix_a,
        wave_a_nm=args.wave_a,
        pix_b=args.pix_b,
        wave_b_nm=args.wave_b,
        wave_pairs=args.wave_pairs,
        wave_degree=args.wave_degree,
        program_id=UUID(args.program) if args.program else None,
        objname=args.objname,
    )
    print(
        f"product={product.id}\ttype={product.product_type}\t"
        f"trace={product.summary.get('trace_y')}\t"
        f"snr={product.summary.get('snr_est')}\t"
        f"sky={product.summary.get('subtract_sky')}\t"
        f"rms_nm={product.summary.get('rms_nm')}\t"
        f"wave={product.summary.get('wave0_nm')}-{product.summary.get('wave1_nm')}nm\t"
        f"uri={product.parameters.get('spectrum_uri')}"
    )
    archive.close()
    return 0


def _cmd_analyze_spectrum_calibrate(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = CalibrateWavelength(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        product_id=UUID(args.product) if args.product else None,
        wave_pairs=args.wave_pairs,
        degree=args.degree,
        lamp_uri=args.lamp_uri,
        catalog=args.catalog,
        wave0_nm=args.wave0,
        wave1_nm=args.wave1,
        program_id=UUID(args.program) if args.program else None,
    )
    print(
        f"product={product.id}\ttype={product.product_type}\t"
        f"method={product.summary.get('method')}\t"
        f"degree={product.summary.get('degree')}\t"
        f"rms_nm={product.summary.get('rms_nm')}\t"
        f"anchors={product.summary.get('n_anchors')}\t"
        f"wave={product.summary.get('wave0_nm')}-{product.summary.get('wave1_nm')}nm\t"
        f"uri={product.parameters.get('spectrum_uri')}"
    )
    archive.close()
    return 0


def _cmd_analyze_spectrum_explain(args: argparse.Namespace) -> int:
    """AC-200: explicar spectrum_report com RAG (narrativa extractiva, sem LLM)."""
    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.knowledge.spectrum_explain import explain_spectrum_report_file

    archive = _open_archive(Path(args.db))
    try:
        result = explain_spectrum_report_file(
            HybridRetriever(archive),
            Path(args.report),
            limit=int(args.limit),
            mode=str(args.mode or "hybrid"),
        )
    finally:
        archive.close()
    print(
        f"explain\tgrounded={result.grounded}\tfeatures={len(result.features_used)}\t"
        f"citations={len(result.citations)}\tmode={result.mode}"
    )
    print("---")
    print(result.format_text(), end="")
    return 0 if result.grounded else 1


def _cmd_analyze_spectrum_report(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    extras: list = []
    if args.extra_products:
        extras = [UUID(x.strip()) for x in args.extra_products.split(",") if x.strip()]
    product = InterpretSpectrum(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        product_id=UUID(args.product) if args.product else None,
        extra_product_ids=extras or None,
        program_id=UUID(args.program) if args.program else None,
        half_width_A=args.half_width,
        snr_min=args.snr_min,
        out_path=Path(args.out) if args.out else None,
    )
    print(
        f"product={product.id}\thint={product.summary.get('class_hint')}\t"
        f"top={product.summary.get('top_line')}\tn_feat={product.summary.get('n_features')}\t"
        f"report={product.parameters.get('report_path')}"
    )
    archive.close()
    return 0


def _cmd_analyze_astrometry(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = MeasureAstrometry(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        x=args.x,
        y=args.y,
        ra0_deg=args.ra0,
        dec0_deg=args.dec0,
        scale_arcsec=args.scale_arcsec,
        pa_deg=args.pa,
        designation=args.designation,
        band=args.band,
        nonsidereal=bool(args.nonsidereal),
        program_id=UUID(args.program) if args.program else None,
    )
    print(
        f"product={product.id}\tra={product.summary.get('ra_deg')}\t"
        f"dec={product.summary.get('dec_deg')}\tmag={product.summary.get('mag')}\t"
        f"epoch={product.summary.get('epoch_utc')}"
    )
    archive.close()
    return 0


def _cmd_analyze_plate_solve(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    nova_cred = cred.get_network("astrometrynet")
    api_key = args.api_key or nova_cred.get("api_key")
    nova_dry = not args.submit
    solver = create_plate_solver(
        args.backend,
        api_key=str(api_key) if api_key else None,
        nova_dry_run=nova_dry if args.backend == "nova" else True,
    )
    product, result = PlateSolve(archive, store, solver).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        ra_hint_deg=args.ra_hint,
        dec_hint_deg=args.dec_hint,
        radius_deg=args.radius,
        scale_low_arcsec=args.scale_low,
        scale_high_arcsec=args.scale_high,
        timeout_s=args.timeout,
        program_id=UUID(args.program) if args.program else None,
    )
    print(
        f"product={product.id}\tbackend={result.backend}\t"
        f"ra={result.ra_center_deg}\tdec={result.dec_center_deg}\t"
        f"scale={result.scale_arcsec}\twcs_uri={product.parameters.get('wcs_uri')}"
    )
    archive.close()
    return 0


def _cmd_analyze_blink(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = BlinkDiff(archive, store).execute(
        workspace_id=ws.id,
        new_uri=args.new_uri,
        ref_uri=args.ref_uri,
        ra0_deg=args.ra0,
        dec0_deg=args.dec0,
        scale_arcsec=args.scale_arcsec,
        pa_deg=args.pa,
        program_id=UUID(args.program) if args.program else None,
        internal_name=args.name,
    )
    print(
        f"product={product.id}\tsnr={product.summary.get('snr')}\t"
        f"ra={product.summary.get('ra_deg')}\tdec={product.summary.get('dec_deg')}\t"
        f"peak={product.summary.get('peak')}"
    )
    archive.close()
    return 0


def _cmd_analyze_sunspots(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = CountSunspots(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        filter_confirmed=bool(args.filter_confirmed),
        no_unfiltered_eyepiece=bool(args.no_unfiltered_eyepiece),
        daytime_acknowledged=bool(args.daytime_ack),
        filter_name=args.filter_name,
        observer=args.observer,
        k=args.k,
        spots=args.spots,
        groups=args.groups,
        program_id=UUID(args.program) if args.program else None,
    )
    print(
        f"product={product.id}\tgroups={product.summary.get('groups')}\t"
        f"spots={product.summary.get('spots')}\twolf_r={product.summary.get('wolf_r')}\t"
        f"filter={product.summary.get('filter_name')}"
    )
    archive.close()
    return 0


def _cmd_observe_log_visual(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    product = LogVisualObservation(archive).execute(
        workspace_id=ws.id,
        object_name=args.object,
        description=args.description,
        conditions=args.conditions or "",
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        target_id=UUID(args.target) if args.target else None,
        observer=args.observer,
        observed_at_utc=args.when,
        magnitude=args.magnitude,
        seeing=args.seeing,
    )
    print(
        f"product={product.id}\tobject={product.summary.get('object')}\t"
        f"at={product.summary.get('observed_at_utc')}"
    )
    archive.close()
    return 0


def _cmd_observe_log_double(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    image = Path(args.image) if args.image else None
    product = LogDoubleMeasure(archive, store).execute(
        workspace_id=ws.id,
        object_name=args.object,
        pa_deg=args.pa,
        sep_arcsec=args.sep,
        epoch_utc=args.when,
        method=args.method,
        mag_primary=args.mag1,
        mag_secondary=args.mag2,
        notes=args.notes or "",
        image_path=image,
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        target_id=UUID(args.target) if args.target else None,
        observer=args.observer,
    )
    print(
        f"product={product.id}\tobject={product.summary.get('object')}\t"
        f"pa={product.summary.get('pa_deg')}\tsep={product.summary.get('sep_arcsec')}\t"
        f"at={product.summary.get('epoch_utc')}"
    )
    archive.close()
    return 0


def _cmd_import_prediction(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = ImportIotaPrediction(archive, store).execute(
        workspace_id=ws.id,
        path=Path(args.path),
        program_id=UUID(args.program) if args.program else None,
        site_id=UUID(args.site) if args.site else None,
    )
    print(
        f"product={product.id}\tevent={product.summary.get('event_id')}\t"
        f"star={product.summary.get('star')}\tasteroid={product.summary.get('asteroid')}"
    )
    archive.close()
    return 0


def _cmd_observe_occultation(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = RegisterOccultationTiming(archive, store).execute(
        workspace_id=ws.id,
        event_id=args.event,
        star=args.star,
        asteroid=args.asteroid,
        result=args.result,
        d_time_utc=args.d_time,
        r_time_utc=args.r_time,
        timesource=args.timesource,
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        prediction_product_id=UUID(args.prediction) if args.prediction else None,
        observer=args.observer,
        notes=args.notes or "",
        video_path=Path(args.video) if args.video else None,
        lc_csv_path=Path(args.lc) if args.lc else None,
        suggest_contacts=bool(args.suggest_contacts),
    )
    print(
        f"product={product.id}\tresult={product.summary.get('result')}\t"
        f"event={product.summary.get('event_id')}\t"
        f"video={product.summary.get('has_video')}\t"
        f"lc_n={product.summary.get('n_lc_points')}"
    )
    archive.close()
    return 0


def _cmd_import_radio(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    kind = str(getattr(args, "kind", None) or "series").lower()
    common = dict(
        workspace_id=ws.id,
        path=Path(args.path),
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        observer=args.observer,
        frequency_mhz=args.freq,
        notes=args.notes or "",
        lab_notes=getattr(args, "lab_notes", "") or "",
    )
    if kind in ("series", "timeseries", "i01"):
        product = ImportRadioTimeseries(archive, store).execute(**common)
    elif kind in ("spectrum", "i02"):
        product = ImportRadioSpectrum(archive, store).execute(**common)
    elif kind in ("scan", "drift", "i03"):
        product = ImportRadioScan(archive, store).execute(**common)
    else:
        print(f"kind invalido: {kind} (series|spectrum|scan)")
        archive.close()
        return 1
    print(
        f"product={product.id}\ttype={product.product_type}\t"
        f"n={product.summary.get('n_points')}\t"
        f"fmt={product.summary.get('format')}\t"
        f"pmin={product.summary.get('power_min')}\t"
        f"pmax={product.summary.get('power_max')}"
    )
    archive.close()
    return 0


def _cmd_import_echelle(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = ImportEchelleOrders(archive, store).execute(
        workspace_id=ws.id,
        path=Path(args.path),
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        observer=args.observer,
        notes=args.notes or "",
    )
    print(
        f"product={product.id}\tn_orders={product.summary.get('n_orders')}\t"
        f"n_files={product.summary.get('n_files')}"
    )
    archive.close()
    return 0


def _cmd_import_speckle(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = ImportSpeckleCube(archive, store).execute(
        workspace_id=ws.id,
        path=Path(args.path),
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        observer=args.observer,
        notes=args.notes or "",
    )
    print(
        f"product={product.id}\tn_frames={product.summary.get('n_frames')}\t"
        f"fmt={product.summary.get('format')}"
    )
    archive.close()
    return 0


def _cmd_import_polar(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = ImportPolarimetrySet(archive, store).execute(
        workspace_id=ws.id,
        path=Path(args.path),
        angles_csv=Path(args.angles) if args.angles else None,
        site_id=UUID(args.site) if args.site else None,
        program_id=UUID(args.program) if args.program else None,
        observer=args.observer,
        notes=args.notes or "",
    )
    print(
        f"product={product.id}\tn_frames={product.summary.get('n_frames')}\t"
        f"P={product.summary.get('P')}\ttheta={product.summary.get('theta_deg')}"
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


def _cmd_contribute_cred_set(args: argparse.Namespace) -> int:
    store = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    vals = {}
    if args.obscode:
        vals["obscode"] = args.obscode
    if args.mpc_code:
        vals["observatory_code"] = args.mpc_code
    if args.email:
        vals["email"] = args.email
    if args.api_key:
        vals["api_key"] = args.api_key
    if args.user_id:
        vals["user_id"] = args.user_id
    if args.groupid is not None:
        vals["groupid"] = args.groupid
    if getattr(args, "observer", None):
        vals["observer"] = args.observer
    if not vals:
        print("nada a gravar (passe --obscode / --mpc-code / --email / --api-key / ...)")
        return 1
    store.set_network(args.network, vals)
    print(f"saved={store.path}\tnetwork={args.network}\tkeys={','.join(vals)}")
    return 0


def _cmd_contribute_cred_show(args: argparse.Namespace) -> int:
    store = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    data = store.load()
    if args.network:
        print(json_dumps_safe({args.network: data.get(args.network) or {}}))
    else:
        # mask secrets
        masked = {}
        for net, vals in data.items():
            m = dict(vals or {})
            if "api_key" in m and m["api_key"]:
                m["api_key"] = "***"
            masked[net] = m
        print(json_dumps_safe(masked))
    return 0


def json_dumps_safe(obj: object) -> str:
    import json

    return json.dumps(obj, indent=2, ensure_ascii=True)


def _cmd_contribute_validate(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    pid = UUID(args.product) if args.product else None
    payload = {}
    if args.obscode:
        payload["obscode"] = args.obscode
    if args.star:
        payload["star"] = args.star
    if args.designation:
        payload["designation"] = args.designation
    if args.obs_code:
        payload["observatory_code"] = args.obs_code
    if args.ra is not None:
        payload["ra_deg"] = args.ra
    if args.dec is not None:
        payload["dec_deg"] = args.dec
    if args.epoch:
        payload["epoch_utc"] = args.epoch
    if args.target:
        payload["target"] = args.target
    result = validate_product_for_network(
        archive, network=args.network, product_id=pid, payload=payload
    )
    for issue in result.issues:
        print(f"{issue.severity}\t{issue.code}\t{issue.message}")
    print(f"ok={result.ok}\tnetwork={args.network}")
    archive.close()
    return 0 if result.ok else 1


def _cmd_contribute_aavso(args: argparse.Namespace) -> int:
    from astrocitizen.adapters.aavso_portal import WEBOBS_URL

    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    obscode = args.obscode or cred.get_network("aavso").get("obscode")
    if not obscode:
        print("falta --obscode ou credentials aavso.obscode")
        archive.close()
        return 1
    chart = getattr(args, "chart", None) or "NA"
    check = validate_product_for_network(
        archive,
        network="aavso",
        product_id=UUID(args.product),
        payload={"obscode": obscode, "star": args.star, "chart": chart},
    )
    for issue in check.issues:
        print(f"{issue.severity}\t{issue.code}\t{issue.message}")
    if not check.ok:
        archive.close()
        return 1
    out = Path(args.out)
    ExportAavso(archive).execute(
        product_id=UUID(args.product),
        star_name=args.star,
        observer_code=str(obscode),
        out_path=out,
        band=args.band,
        chart=chart,
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/aavso/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="aavso",
        status="validated",
        artifact_uri=uri,
        product_id=UUID(args.product),
        payload_summary={
            "star": args.star,
            "obscode": obscode,
            "chart": chart,
            "note": "upload via WebObs (oficial)",
        },
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tsubmission={sub.id}\twebobs={WEBOBS_URL}")
    if getattr(args, "open_webobs", False):
        import webbrowser

        webbrowser.open(WEBOBS_URL)
        print(f"opened={WEBOBS_URL}")
    archive.close()
    return 0


def _cmd_contribute_mpc(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    mpc_cred = cred.get_network("mpc")
    code = args.obs_code or mpc_cred.get("observatory_code")
    email = args.email or mpc_cred.get("email")
    if not code:
        print("falta --obs-code ou credentials mpc.observatory_code")
        archive.close()
        return 1
    designation = args.designation
    epoch = args.epoch
    ra = args.ra
    dec = args.dec
    mag = args.mag
    band = args.band
    product_id = None
    if args.product:
        product = archive.get_analysis_product(UUID(args.product))
        if product is None:
            print(f"produto nao encontrado: {args.product}")
            archive.close()
            return 1
        product_id = product.id
        designation = designation or str(product.parameters.get("designation") or "NEO")
        epoch = epoch or str(product.summary.get("epoch_utc") or "")
        ra = ra if ra is not None else product.summary.get("ra_deg")
        dec = dec if dec is not None else product.summary.get("dec_deg")
        mag = mag if mag is not None else product.summary.get("mag")
        band = band or str(product.parameters.get("band") or "R")
    if ra is None or dec is None or not epoch:
        print("falta RA/Dec/epoch (--ra/--dec/--epoch ou --product astrometry)")
        archive.close()
        return 1
    if not designation:
        print("falta --designation")
        archive.close()
        return 1
    check = validate_product_for_network(
        archive,
        network="mpc",
        product_id=product_id,
        payload={
            "observatory_code": code,
            "designation": designation,
            "ra_deg": ra,
            "dec_deg": dec,
            "epoch_utc": epoch,
        },
    )
    for issue in check.issues:
        print(f"{issue.severity}\t{issue.code}\t{issue.message}")
    if not check.ok:
        archive.close()
        return 1
    out = Path(args.out)
    write_ades_psv(
        out,
        observatory_code=str(code),
        designation=designation,
        observations=[
            {
                "epoch_utc": epoch,
                "ra_deg": float(ra),
                "dec_deg": float(dec),
                "mag": mag,
                "band": band,
                "ra_err_arcsec": args.ra_err,
                "dec_err_arcsec": args.dec_err,
            }
        ],
        submitter="AstroCitizen",
    )
    dry = not args.submit
    if not dry and not email:
        print("submit real requer --email ou credentials mpc.email")
        archive.close()
        return 1
    meta = MpcAdesSubmitter().submit(
        out,
        email=str(email or "dry-run@example.com"),
        obj_type=args.obj_type,
        dry_run=dry,
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/mpc/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="mpc",
        status=str(meta.get("status") or "draft"),
        artifact_uri=uri,
        product_id=product_id,
        payload_summary={"designation": designation, "meta": meta},
        remote_ack=str(meta.get("response") or meta.get("ack") or "")[:500] or None,
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tstatus={sub.status}\tsubmission={sub.id}")
    archive.close()
    return 0 if sub.status in ("dry_run", "submitted", "draft") else 2


def _cmd_contribute_tns(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    tns_cred = cred.get_network("tns")
    api_key = args.api_key or tns_cred.get("api_key") or "dry-run-key"
    user_id = args.user_id or tns_cred.get("user_id") or "0"
    groupid = args.groupid if args.groupid is not None else tns_cred.get("groupid", 0)
    ra = args.ra
    dec = args.dec
    mag = args.mag
    internal_name = args.internal_name
    product_id = None
    if args.product:
        product = archive.get_analysis_product(UUID(args.product))
        if product is None:
            print(f"produto nao encontrado: {args.product}")
            archive.close()
            return 1
        product_id = product.id
        ra = ra if ra is not None else product.summary.get("ra_deg")
        dec = dec if dec is not None else product.summary.get("dec_deg")
        internal_name = internal_name or str(
            product.parameters.get("internal_name") or "AstroCitizen-AT"
        )
    if ra is None or dec is None:
        print("falta RA/Dec (--ra/--dec ou --product blink_candidate)")
        archive.close()
        return 1
    if mag is None:
        mag = 99.0
    report = format_tns_at_report(
        ra_deg=float(ra),
        dec_deg=float(dec),
        groupid=int(groupid),
        reporter=args.reporter,
        discovery_mag=float(mag),
        filter_value=args.filter,
        internal_name=internal_name,
    )
    out = Path(args.out)
    write_tns_report(out, report)
    dry = not args.submit
    if not dry and (api_key == "dry-run-key" or user_id == "0"):
        print("submit real requer --api-key e --user-id (ou credentials tns)")
        archive.close()
        return 1
    meta = TnsClient(
        api_key=str(api_key),
        user_id=str(user_id),
        sandbox=not args.prod,
    ).submit_report(report, dry_run=dry)
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/tns/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="tns",
        status=str(meta.get("status") or "draft"),
        artifact_uri=uri,
        product_id=product_id,
        payload_summary={"ra": float(ra), "dec": float(dec), "meta": meta},
        remote_ack=str(meta.get("response") or "")[:500] or None,
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tstatus={sub.status}\tsubmission={sub.id}")
    archive.close()
    return 0


def _cmd_contribute_form_schema(args: argparse.Namespace) -> int:
    import json

    from astrocitizen.integrations.form_schemas import list_form_networks, load_form_schema

    if getattr(args, "list_networks", False):
        for name in list_form_networks():
            print(name)
        return 0
    network = (args.network or "").strip().lower()
    if not network:
        print("indique --network ou --list")
        return 1
    schema = load_form_schema(network)
    print(json.dumps(schema, ensure_ascii=False, indent=2))
    return 0


def _cmd_catalog_cache_get(args: argparse.Namespace) -> int:
    import json

    archive = _open_archive(Path(args.db))
    archive.migrate()
    row = archive.get_institutional_cache(
        provider=args.provider, object_id=args.id
    )
    archive.close()
    if row is None:
        print("cache miss")
        return 1
    print(json.dumps(row, ensure_ascii=False, indent=2))
    return 0


def _cmd_catalog_cache_list(args: argparse.Namespace) -> int:
    import json

    archive = _open_archive(Path(args.db))
    archive.migrate()
    rows = archive.list_institutional_cache(
        provider=args.provider, limit=int(args.limit)
    )
    archive.close()
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def _cmd_contribute_list(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    rows = archive.list_network_submissions(ws.id, network=args.network)
    for s in rows:
        print(
            f"{s.created_at}\t{s.network}\t{s.status}\t{s.id}\t"
            f"{(s.artifact_uri or '-')[:60]}"
        )
    archive.close()
    return 0


def _cmd_contribute_bess(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    observer = args.observer or cred.get_network("bess").get("observer") or "AstroCitizen"
    out = Path(args.out)
    product_id = None
    objname = args.objname
    if args.product:
        product = archive.get_analysis_product(UUID(args.product))
        if product is None:
            print(f"produto nao encontrado: {args.product}")
            archive.close()
            return 1
        if product.product_type != "spectrum_1d":
            print(f"produto nao e spectrum_1d: {product.product_type}")
            archive.close()
            return 1
        product_id = product.id
        objname = objname or str(product.parameters.get("objname") or "SPEC")
        spectrum_uri = product.parameters.get("spectrum_uri")
        if not spectrum_uri:
            print("produto sem spectrum_uri")
            archive.close()
            return 1
        store0 = LocalArtifactStore(Path(args.artifacts))
        annotate_existing_fits(
            store0.resolve(str(spectrum_uri)),
            out,
            observer=str(observer),
            site=args.site,
            instrument=args.instrument,
        )
    elif args.fits:
        annotate_existing_fits(
            Path(args.fits),
            out,
            observer=str(observer),
            site=args.site,
            instrument=args.instrument,
        )
    else:
        import numpy as np

        n = max(int(args.npix), 2)
        wave = np.linspace(args.wave0, args.wave1, n)
        flux = np.ones(n, dtype=float)
        write_bess_fits(
            out,
            objname=objname,
            observer=str(observer),
            date_obs=args.date_obs,
            exptime_s=args.exptime,
            wavelength_nm=wave,
            flux=flux,
            site=args.site or "AstroCitizen",
            instrument=args.instrument or "AstroCitizen-spec",
            ra_deg=args.ra,
            dec_deg=args.dec,
        )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/bess/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="bess",
        status="draft",
        artifact_uri=uri,
        product_id=product_id,
        payload_summary={"objname": objname, "note": "upload BeSS portal"},
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tsubmission={sub.id}\tportal=http://basebe.obspm.fr/")
    archive.close()
    return 0


def _cmd_contribute_exoclock(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    observer = args.observer or cred.get_network("exoclock").get("observer") or "AstroCitizen"
    out = Path(args.out)
    ExportExoclock(archive).execute(
        product_id=UUID(args.product),
        target=args.target,
        out_path=out,
        telescope=args.telescope,
        observer=str(observer),
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/exoclock/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="exoclock",
        status="draft",
        artifact_uri=uri,
        product_id=UUID(args.product),
        payload_summary={"target": args.target, "note": "upload ExoClock"},
    )
    archive.save_network_submission(sub)
    print(
        f"wrote={out}\turi={uri}\tsubmission={sub.id}\t"
        f"upload=https://www.exoclock.space/upload/"
    )
    archive.close()
    return 0


def _cmd_contribute_iota(args: argparse.Namespace) -> int:
    import shutil

    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    site = _resolve_site(archive, ws, args.site)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    observer = args.observer or cred.get_network("iota").get("observer") or "AstroCitizen"
    pack_dir = Path(args.out)
    write_iota_pack(
        pack_dir,
        event_id=args.event,
        star=args.star,
        asteroid=args.asteroid,
        observer=str(observer),
        latitude_deg=site.latitude_deg,
        longitude_deg=site.longitude_deg,
        elevation_m=site.elevation_m,
        result=args.result,
        d_time_utc=args.d_time,
        r_time_utc=args.r_time,
    )
    zip_base = pack_dir if pack_dir.suffix == "" else pack_dir.with_suffix("")
    zip_path = Path(shutil.make_archive(str(zip_base), "zip", root_dir=pack_dir))
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(zip_path, key=f"export/iota/{zip_path.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="iota",
        status="draft",
        artifact_uri=uri,
        payload_summary={"event": args.event, "result": args.result},
    )
    archive.save_network_submission(sub)
    print(f"pack={pack_dir}\tzip={zip_path}\turi={uri}\tsubmission={sub.id}")
    archive.close()
    return 0


def _cmd_contribute_solar(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    observer = args.observer or cred.get_network("solar").get("observer")
    out = Path(args.out)
    ExportSolarReport(archive).execute(
        product_id=UUID(args.product),
        out_path=out,
        observer=str(observer) if observer else None,
        site=args.site,
        notes=args.notes,
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/solar/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="solar",
        status="draft",
        artifact_uri=uri,
        product_id=UUID(args.product),
        payload_summary={"note": "upload rede solar amadora / arquivo local"},
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tsubmission={sub.id}")
    archive.close()
    return 0


def _cmd_contribute_wds(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    wds_cred = cred.get_network("wds")
    product_id = UUID(args.product)
    check = validate_product_for_network(
        archive,
        network="wds",
        product_id=product_id,
        payload={"object": args.object} if args.object else {},
    )
    for issue in check.issues:
        print(f"{issue.severity}\t{issue.code}\t{issue.message}")
    if not check.ok:
        archive.close()
        return 1
    overrides: dict = {}
    if args.object:
        overrides["object_name"] = args.object
    if args.observer or wds_cred.get("observer"):
        overrides["observer"] = args.observer or wds_cred.get("observer")
    if args.observatory:
        overrides["observatory"] = args.observatory
    if args.discoverer:
        overrides["discoverer"] = args.discoverer
    if args.notes:
        overrides["notes"] = args.notes
    out = Path(args.out)
    ExportWds(archive).execute(
        product_id=product_id,
        out_path=out,
        overrides=overrides or None,
        write_csv=not args.no_csv,
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/wds/{out.name}")
    csv_path = out.with_suffix(".csv")
    if csv_path.is_file():
        store.put(csv_path, key=f"export/wds/{csv_path.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="wds",
        status="validated",
        artifact_uri=uri,
        product_id=product_id,
        payload_summary={
            "object": args.object,
            "note": "submit manual USNO / WDS maintainer",
        },
    )
    archive.save_network_submission(sub)
    print(
        f"wrote={out}\turi={uri}\tsubmission={sub.id}\t"
        "submit=https://www.astro.gsu.edu/wds/"
    )
    archive.close()
    return 0


def _cmd_contribute_cobs(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    cobs_cred = cred.get_network("cobs")
    product_id = UUID(args.product) if args.product else None
    overrides: dict = {}
    for key in (
        "designation",
        "mag_method",
        "comp_cat",
        "instr_type",
        "dc",
        "obscode",
        "observer",
        "location",
        "notes",
    ):
        val = getattr(args, key, None)
        if val:
            overrides[key] = val
    if args.epoch:
        overrides["epoch_utc"] = args.epoch
    if args.mag is not None:
        overrides["mag"] = args.mag
    for key in (
        "aperture_cm",
        "focal_ratio",
        "power_or_exptime",
        "coma_arcmin",
        "tail_deg",
        "tail_pa",
    ):
        val = getattr(args, key, None)
        if val is not None:
            overrides[key] = val
    if not overrides.get("obscode") and cobs_cred.get("obscode"):
        overrides["obscode"] = cobs_cred["obscode"]
    if not overrides.get("observer") and cobs_cred.get("observer"):
        overrides["observer"] = cobs_cred["observer"]
    check = validate_product_for_network(
        archive,
        network="cobs",
        product_id=product_id,
        payload=overrides,
    )
    for issue in check.issues:
        print(f"{issue.severity}\t{issue.code}\t{issue.message}")
    if not check.ok:
        archive.close()
        return 1
    out = Path(args.out)
    ExportCobs(archive).execute(
        product_id=product_id,
        out_path=out,
        overrides=overrides or None,
        write_csv=not args.no_csv,
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/cobs/{out.name}")
    csv_path = out.with_suffix(".csv")
    if csv_path.is_file():
        store.put(csv_path, key=f"export/cobs/{csv_path.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="cobs",
        status="validated",
        artifact_uri=uri,
        product_id=product_id,
        payload_summary={
            "designation": overrides.get("designation"),
            "note": "submit manual https://www.cobs.si/",
        },
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tsubmission={sub.id}\tsubmit=https://www.cobs.si/")
    archive.close()
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


def _cmd_knowledge_validate(args: argparse.Namespace) -> int:
    from astrocitizen.knowledge import default_kb_root, validate_kb_scaffold

    root = Path(args.kb_root) if args.kb_root else default_kb_root()
    errors = validate_kb_scaffold(root)
    if errors:
        for err in errors:
            print(f"error\t{err}")
        return 1
    print(f"ok\tkb_root={root}")
    return 0


def _cmd_knowledge_ingest(args: argparse.Namespace) -> int:
    from astrocitizen.knowledge import default_kb_root, ingest_sources

    root = Path(args.kb_root) if args.kb_root else default_kb_root()
    archive = None
    write_db = not args.no_db and not args.dry_run
    if write_db:
        archive = _open_archive(Path(args.db))
        archive.migrate()
    try:
        report = ingest_sources(
            archive=archive,
            kb_root=root,
            trust_tiers=(str(args.tier),),
            source_id=args.source_id,
            write_files=not args.no_files,
            write_db=write_db,
            dry_run=bool(args.dry_run),
            corpus_version=str(args.corpus_version),
        )
    finally:
        if archive is not None:
            archive.close()
    for src in report.sources:
        print(
            f"source\t{src['source_id']}\tchunks={src['n_chunks']}\t"
            f"hash={src['content_hash']}"
        )
    for err in report.errors:
        print(f"error\t{err}")
    print(
        f"summary\tsources={report.n_sources}\tchunks={report.n_chunks}\t"
        f"corpus={report.corpus_version}\tok={report.ok}"
    )
    return 0 if report.ok or (args.dry_run and report.n_chunks > 0) else 1


def _cmd_knowledge_index(args: argparse.Namespace) -> int:
    from astrocitizen.knowledge import default_kb_root, rebuild_fts_index

    root = Path(args.kb_root) if args.kb_root else default_kb_root()
    archive = _open_archive(Path(args.db))
    archive.migrate()
    try:
        report = rebuild_fts_index(
            archive, kb_root=root, update_manifest=not args.no_manifest
        )
    finally:
        archive.close()
    print(
        f"fts\tn_rows={report.n_rows}\tbuilt={report.built_utc}\t"
        f"engine={report.engine}\tok={report.n_rows > 0}"
    )
    return 0 if report.n_rows > 0 else 1


def _cmd_knowledge_search(args: argparse.Namespace) -> int:
    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.ports.retriever import RetrieveFilters

    archive = _open_archive(Path(args.db))
    archive.migrate()
    try:
        retriever = HybridRetriever(archive)
        hits = retriever.search(
            str(args.query),
            limit=int(args.limit),
            filters=RetrieveFilters(
                trust_tier=args.tier,
                source_id=args.source_id,
                lang=args.lang,
                po_id=args.po_id,
                network=args.network,
                topic=args.topic,
            ),
            mode=str(args.mode or "hybrid"),
        )
    finally:
        archive.close()
    if not hits:
        print("hits\t0")
        return 1
    print(f"hits\t{len(hits)}\tmode={args.mode}")
    for h in hits:
        title = (h.title or "").replace("\t", " ")[:80]
        snip = (h.snippet or "").replace("\n", " ").replace("\t", " ")[:160]
        score = f"{h.score:.4f}" if h.score is not None else "n/a"
        print(
            f"hit\t{h.chunk_id}\t{h.source_id}\t{h.trust_tier}\t"
            f"score={score}\t{title}\t{snip}"
        )
    return 0


def _cmd_knowledge_embed(args: argparse.Namespace) -> int:
    from astrocitizen.knowledge import default_kb_root
    from astrocitizen.knowledge.embed_index import rebuild_embeddings

    root = Path(args.kb_root) if args.kb_root else default_kb_root()
    archive = _open_archive(Path(args.db))
    archive.migrate()
    try:
        report = rebuild_embeddings(
            archive, kb_root=root, update_manifest=not args.no_manifest
        )
    finally:
        archive.close()
    print(
        f"embed\tn_rows={report.n_rows}\tmodel={report.model_id}\t"
        f"dim={report.dim}\tbuilt={report.built_utc}\tok={report.n_rows > 0}"
    )
    return 0 if report.n_rows > 0 else 1


def _cmd_knowledge_get(args: argparse.Namespace) -> int:
    from astrocitizen.adapters.sqlite.fts_retriever import SqliteFtsRetriever

    archive = _open_archive(Path(args.db))
    archive.migrate()
    try:
        cite = SqliteFtsRetriever(archive).get_chunk(str(args.chunk_id))
    finally:
        archive.close()
    if cite is None:
        print(f"error\tchunk_not_found\t{args.chunk_id}")
        return 1
    print(
        f"chunk\t{cite.chunk_id}\t{cite.source_id}\t{cite.trust_tier}\t"
        f"{cite.citation_label()}"
    )
    if cite.title:
        print(f"title\t{cite.title}")
    if cite.path:
        print(f"path\t{cite.path}")
    if cite.topics:
        print(f"topics\t{','.join(cite.topics)}")
    print("---")
    print(cite.body or "")
    return 0


def _cmd_knowledge_sources(args: argparse.Namespace) -> int:
    from astrocitizen.adapters.sqlite.fts_retriever import SqliteFtsRetriever

    archive = _open_archive(Path(args.db))
    archive.migrate()
    try:
        sources = SqliteFtsRetriever(archive).list_sources(trust_tier=args.tier)
    finally:
        archive.close()
    print(f"sources\t{len(sources)}")
    for s in sources:
        topics = ",".join(s.get("topics") or [])
        print(
            f"source\t{s['source_id']}\t{s['trust_tier']}\t"
            f"{s.get('title') or ''}\t{topics}"
        )
    return 0 if sources else 1


def _cmd_knowledge_ask(args: argparse.Namespace) -> int:
    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.knowledge.assistant import answer_help
    from astrocitizen.ports.retriever import RetrieveFilters

    archive = _open_archive(Path(args.db))
    try:
        ans = answer_help(
            HybridRetriever(archive),
            str(args.question),
            limit=int(args.limit),
            mode=str(args.mode or "hybrid"),  # type: ignore[arg-type]
            filters=RetrieveFilters(
                trust_tier=args.tier,
                source_id=args.source_id,
                lang=args.lang,
                po_id=args.po_id,
                network=args.network,
                topic=args.topic,
            ),
        )
    finally:
        archive.close()
    print(f"grounded\t{ans.grounded}\tmode={ans.mode}\tcitations={len(ans.citations)}")
    if ans.refusal_reason:
        print(f"refusal\t{ans.refusal_reason}")
    print("---")
    print(ans.format_text(), end="")
    return 0 if ans.grounded else 1


def _cmd_knowledge_eval_gold(args: argparse.Namespace) -> int:
    import json

    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.knowledge import default_kb_root
    from astrocitizen.knowledge.eval_gold import evaluate_gold, write_eval_report

    root = Path(args.kb_root) if args.kb_root else default_kb_root()
    archive = _open_archive(Path(args.db))
    try:
        report = evaluate_gold(
            HybridRetriever(archive),
            kb_root=root,
            limit=int(args.limit),
            mode=str(args.mode or "hybrid"),
        )
    finally:
        archive.close()
    if args.out:
        write_eval_report(report, Path(args.out))
    print(
        f"gold\tset={report.set_id}\tn={report.n_questions}\t"
        f"hits={report.n_hits}\trate={report.citation_rate:.3f}\t"
        f"target={report.target}\tpassed={report.passed}"
    )
    for r in report.results:
        mark = "HIT" if r.hit else "MISS"
        print(
            f"q\t{r.question_id}\t{mark}\tcited={','.join(r.cited_source_ids) or '-'}\t"
            f"expected={','.join(r.expected_source_ids)}"
        )
    if args.json:
        print("---")
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0 if report.passed else 1


def _cmd_knowledge_glossary(args: argparse.Namespace) -> int:
    import json

    from astrocitizen.knowledge import default_kb_root
    from astrocitizen.knowledge.glossary import (
        entry_to_dict,
        get_entry,
        list_entries,
        search_entries,
        sync_glossary_chunks,
    )

    root = Path(args.kb_root) if args.kb_root else default_kb_root()
    action = str(args.glossary_cmd)
    if action == "sync":
        report = sync_glossary_chunks(kb_root=root)
        print(
            f"glossary\tsync\tentries={report.n_entries}\t"
            f"chunks={report.n_chunks_written}\tok={report.n_chunks_written > 0}"
        )
        return 0 if report.n_chunks_written > 0 else 1
    if action == "get":
        hit = get_entry(str(args.term), kb_root=root, lang=args.lang)
        if hit is None:
            print(f"error\tnot_found\t{args.term}")
            return 1
        print(json.dumps(entry_to_dict(hit), ensure_ascii=False, indent=2))
        return 0
    # list / search
    if args.query:
        entries = search_entries(
            str(args.query),
            kb_root=root,
            limit=int(args.limit),
            topic=args.topic,
            network=args.network,
            po_id=args.po_id,
        )
    else:
        entries = list_entries(root)[: int(args.limit)]
    print(f"entries\t{len(entries)}")
    for e in entries:
        print(f"term\t{e.term_id}\t{e.term}\t{e.definition[:100]}")
    return 0 if entries else 1


def _cmd_knowledge_mcp_tools(args: argparse.Namespace) -> int:
    from astrocitizen.knowledge.mcp_tools import TOOL_DEFS

    print(f"tools\t{len(TOOL_DEFS)}")
    for t in TOOL_DEFS:
        print(f"tool\t{t['name']}\t{t['description'][:80]}")
    return 0


def _cmd_knowledge_mcp_call(args: argparse.Namespace) -> int:
    import json

    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.knowledge.mcp_tools import KbMcpServer, RateLimiter

    raw = args.arguments or "{}"
    try:
        arguments = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"error\tinvalid_json\t{exc}")
        return 1
    if not isinstance(arguments, dict):
        print("error\targuments_must_be_object")
        return 1
    archive = _open_archive(Path(args.db))
    archive.migrate()
    try:
        server = KbMcpServer(
            HybridRetriever(archive),
            rate_limiter=RateLimiter(
                max_calls=int(args.rate_limit), window_s=float(args.rate_window)
            ),
        )
        result = server.call_tool(str(args.tool), arguments)
    finally:
        archive.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


def _cmd_knowledge_mcp_serve(args: argparse.Namespace) -> int:
    """Servidor MCP stdio minimo (JSON-RPC linha a linha)."""
    import json
    import sys

    from astrocitizen.adapters.sqlite.hybrid_retriever import HybridRetriever
    from astrocitizen.knowledge.mcp_tools import (
        KbMcpServer,
        RateLimiter,
        handle_mcp_jsonrpc,
    )

    archive = _open_archive(Path(args.db))
    archive.migrate()
    server = KbMcpServer(
        HybridRetriever(archive),
        rate_limiter=RateLimiter(
            max_calls=int(args.rate_limit), window_s=float(args.rate_window)
        ),
    )
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                err = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                print(json.dumps(err), flush=True)
                continue
            response = handle_mcp_jsonrpc(server, message)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
    finally:
        archive.close()
    return 0


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
    p_tadd.add_argument(
        "--resolve-vsx",
        action="store_true",
        help="Resolver via VSX (AAVSO; AUID/tipo/periodo)",
    )
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

    p_obs = sub.add_parser("observe", help="Entrada observacional (visual / ocultacao)")
    obs_sub = p_obs.add_subparsers(dest="observe_cmd", required=True)
    p_ov = obs_sub.add_parser("log-visual", help="Log visual PO-F03")
    _add_db_arg(p_ov)
    p_ov.add_argument("--object", required=True, help="Designacao do objecto")
    p_ov.add_argument("--description", required=True)
    p_ov.add_argument("--conditions", default="")
    p_ov.add_argument("--seeing", default=None)
    p_ov.add_argument("--magnitude", type=float, default=None)
    p_ov.add_argument("--observer", default="AstroCitizen")
    p_ov.add_argument("--when", default=None, help="UTC ISO")
    p_ov.add_argument("--site", default=None, help="UUID site")
    p_ov.add_argument("--program", default=None, help="UUID programa")
    p_ov.add_argument("--target", default=None, help="UUID alvo")
    p_ov.set_defaults(func=_cmd_observe_log_visual)
    p_od = obs_sub.add_parser("log-double", help="Medida dupla PO-G01 (PA/sep)")
    _add_db_arg(p_od)
    p_od.add_argument("--object", required=True, help="WDS / designacao")
    p_od.add_argument("--pa", type=float, required=True, help="PA degrees [0,360)")
    p_od.add_argument("--sep", type=float, required=True, help="sep arcsec > 0")
    p_od.add_argument(
        "--method",
        default="micrometer",
        choices=("micrometer", "imaging_manual", "other"),
    )
    p_od.add_argument("--mag1", type=float, default=None, help="mag primaria")
    p_od.add_argument("--mag2", type=float, default=None, help="mag secundaria")
    p_od.add_argument("--notes", default="")
    p_od.add_argument("--image", default=None, help="FITS/imagem opcional")
    p_od.add_argument("--observer", default="AstroCitizen")
    p_od.add_argument("--when", default=None, help="UTC ISO epoch")
    p_od.add_argument("--site", default=None)
    p_od.add_argument("--program", default=None)
    p_od.add_argument("--target", default=None)
    p_od.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_od.set_defaults(func=_cmd_observe_log_double)
    p_oo = obs_sub.add_parser("occultation", help="Contactos D/R IOTA (PO-D01)")
    _add_db_arg(p_oo)
    p_oo.add_argument("--event", required=True, help="EventID")
    p_oo.add_argument("--star", required=True)
    p_oo.add_argument("--asteroid", required=True)
    p_oo.add_argument(
        "--result",
        default="positive",
        choices=("positive", "negative", "missed"),
    )
    p_oo.add_argument("--d-time", default=None, help="UTC ISO D")
    p_oo.add_argument("--r-time", default=None, help="UTC ISO R")
    p_oo.add_argument(
        "--timesource",
        default="NTP",
        choices=("NTP", "GPS", "VTI", "manual", "PC"),
    )
    p_oo.add_argument("--observer", default="AstroCitizen")
    p_oo.add_argument("--notes", default="")
    p_oo.add_argument("--site", default=None)
    p_oo.add_argument("--program", default=None)
    p_oo.add_argument("--prediction", default=None, help="UUID produto previsao")
    p_oo.add_argument("--video", default=None, help="SER/AVI/MP4 (IN-VID)")
    p_oo.add_argument("--lc", default=None, help="CSV curva de luz")
    p_oo.add_argument(
        "--suggest-contacts",
        action="store_true",
        help="Estimar D/R a partir do LC (heuristica)",
    )
    p_oo.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_oo.set_defaults(func=_cmd_observe_occultation)

    p_imp = sub.add_parser(
        "import",
        help="Importar dados (IN-IMP / IN-PRED / IN-RAD / P4)",
    )
    imp_sub = p_imp.add_subparsers(dest="import_cmd", required=True)
    p_if = imp_sub.add_parser("fits", help="Importar FITS -> Observation + Artifact")
    _add_db_arg(p_if)
    p_if.add_argument("--path", required=True, help="Ficheiro FITS ou directorio")
    p_if.add_argument("--recursive", action="store_true")
    p_if.add_argument("--limit", type=int, default=None)
    p_if.add_argument("--site", default=None)
    p_if.add_argument("--program", default=None, help="UUID do programa")
    p_if.add_argument("--target", default=None, help="UUID do alvo")
    p_if.add_argument("--frame-type", default=None, help="light/bias/dark/flat")
    p_if.add_argument("--simulated", action="store_true")
    p_if.add_argument("--notes", default=None)
    p_if.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_if.set_defaults(func=_cmd_import_fits)
    p_ip = imp_sub.add_parser(
        "prediction",
        help="Importar previsao IOTA (IN-PRED / AC-120)",
    )
    _add_db_arg(p_ip)
    p_ip.add_argument("--path", required=True, help="TXT KEY:value ou CSV")
    p_ip.add_argument("--site", default=None)
    p_ip.add_argument("--program", default=None)
    p_ip.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ip.set_defaults(func=_cmd_import_prediction)
    p_ir = imp_sub.add_parser(
        "radio", help="Importar radio CSV/HDF5 (IN-RAD / PO-I01..I04)"
    )
    _add_db_arg(p_ir)
    p_ir.add_argument("--path", required=True, help=".csv/.txt ou .h5/.hdf5 (series)")
    p_ir.add_argument(
        "--kind",
        default="series",
        choices=("series", "spectrum", "scan"),
        help="series=PO-I01 | spectrum=PO-I02 | scan=PO-I03",
    )
    p_ir.add_argument("--site", default=None)
    p_ir.add_argument("--program", default=None)
    p_ir.add_argument("--observer", default="AstroCitizen")
    p_ir.add_argument("--freq", type=float, default=None, help="MHz")
    p_ir.add_argument("--notes", default="")
    p_ir.add_argument(
        "--lab-notes",
        default="",
        help="Notas de construcao / lab (PO-I04)",
    )
    p_ir.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ir.set_defaults(func=_cmd_import_radio)
    p_ie = imp_sub.add_parser("echelle", help="Importar ordens echelle FITS (PO-B07)")
    _add_db_arg(p_ie)
    p_ie.add_argument("--path", required=True, help="FITS multi-ext ou pasta")
    p_ie.add_argument("--site", default=None)
    p_ie.add_argument("--program", default=None)
    p_ie.add_argument("--observer", default="AstroCitizen")
    p_ie.add_argument("--notes", default="")
    p_ie.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ie.set_defaults(func=_cmd_import_echelle)
    p_is = imp_sub.add_parser("speckle", help="Importar cubo/stack/video (PO-G02)")
    _add_db_arg(p_is)
    p_is.add_argument("--path", required=True, help="FITS cubo, pasta ou SER")
    p_is.add_argument("--site", default=None)
    p_is.add_argument("--program", default=None)
    p_is.add_argument("--observer", default="AstroCitizen")
    p_is.add_argument("--notes", default="")
    p_is.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_is.set_defaults(func=_cmd_import_speckle)
    p_ipo = imp_sub.add_parser("polar", help="Importar set polarimetro (PO-H01)")
    _add_db_arg(p_ipo)
    p_ipo.add_argument("--path", required=True, help="FITS ou pasta de frames")
    p_ipo.add_argument("--angles", default=None, help="CSV filename,angle_deg")
    p_ipo.add_argument("--site", default=None)
    p_ipo.add_argument("--program", default=None)
    p_ipo.add_argument("--observer", default="AstroCitizen")
    p_ipo.add_argument("--notes", default="")
    p_ipo.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ipo.set_defaults(func=_cmd_import_polar)

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

    p_an = sub.add_parser("analyze", help="Analise (fotometria / espectro / astrometria / blink)")
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
    p_sp = an_sub.add_parser("spectrum", help="Extracao espectro 1D (AC-100 / PO-B01)")
    _add_db_arg(p_sp)
    p_sp.add_argument("--fits-uri", required=True)
    p_sp.add_argument(
        "--trace-y",
        type=float,
        default=None,
        help="Posicao do trace (pix); omitir com --auto-trace",
    )
    p_sp.add_argument(
        "--auto-trace",
        action="store_true",
        help="Detectar pico espacial automaticamente",
    )
    p_sp.add_argument("--half-width", type=int, default=3)
    p_sp.add_argument("--axis", choices=("x", "y"), default="x")
    p_sp.add_argument(
        "--no-sky",
        action="store_true",
        help="Desligar subtracao de ceu (default: ligada)",
    )
    p_sp.add_argument("--sky-offset", type=int, default=None, help="pix do centro")
    p_sp.add_argument("--sky-width", type=int, default=None, help="half-width ceu")
    p_sp.add_argument("--wave0", type=float, default=None, help="nm")
    p_sp.add_argument("--wave1", type=float, default=None, help="nm")
    p_sp.add_argument("--pix-a", type=float, default=None)
    p_sp.add_argument("--wave-a", type=float, default=None, help="nm")
    p_sp.add_argument("--pix-b", type=float, default=None)
    p_sp.add_argument("--wave-b", type=float, default=None, help="nm")
    p_sp.add_argument(
        "--wave-pairs",
        default=None,
        help="AC-101 pares pix:nm,pix:nm,... (polinomio)",
    )
    p_sp.add_argument(
        "--wave-degree",
        type=int,
        default=None,
        help="grau 1..3 para --wave-pairs (default auto)",
    )
    p_sp.add_argument("--objname", default=None)
    p_sp.add_argument("--program", default=None)
    p_sp.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_sp.set_defaults(func=_cmd_analyze_spectrum)
    p_sc = an_sub.add_parser(
        "spectrum-calibrate",
        help="Calibracao λ de espectro 1D (AC-101)",
    )
    _add_db_arg(p_sc)
    p_sc.add_argument("--fits-uri", default=None, help="FITS 1D ciencia")
    p_sc.add_argument("--product", default=None, help="Produto spectrum_1d")
    p_sc.add_argument(
        "--wave-pairs",
        default=None,
        help="pix:nm,pix:nm,...",
    )
    p_sc.add_argument("--degree", type=int, default=None, help="1..3")
    p_sc.add_argument("--lamp-uri", default=None, help="FITS 1D lamp (mesmo n_pix)")
    p_sc.add_argument(
        "--catalog",
        default="neon",
        choices=("neon", "ne", "hg", "mercury"),
    )
    p_sc.add_argument("--wave0", type=float, default=None, help="seed nm (lamp)")
    p_sc.add_argument("--wave1", type=float, default=None, help="seed nm (lamp)")
    p_sc.add_argument("--program", default=None)
    p_sc.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_sc.set_defaults(func=_cmd_analyze_spectrum_calibrate)
    p_sr = an_sub.add_parser(
        "spectrum-report",
        help="Interpretacao espectral (linhas / SN-ARAS / multi-epoca)",
    )
    _add_db_arg(p_sr)
    p_sr.add_argument("--fits-uri", default=None, help="FITS 1D")
    p_sr.add_argument("--product", default=None, help="Produto spectrum_1d")
    p_sr.add_argument(
        "--extra-products",
        default=None,
        help="UUIDs extra separados por virgula (multi-epoca)",
    )
    p_sr.add_argument("--half-width", type=float, default=40.0, help="Angstrom")
    p_sr.add_argument("--snr-min", type=float, default=3.0)
    p_sr.add_argument("--out", default=None, help="Ficheiro .txt do relatorio")
    p_sr.add_argument("--program", default=None)
    p_sr.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_sr.set_defaults(func=_cmd_analyze_spectrum_report)
    p_sx = an_sub.add_parser(
        "spectrum-explain",
        help="Explicar spectrum_report com RAG KB (AC-200; sem LLM)",
    )
    _add_db_arg(p_sx)
    p_sx.add_argument(
        "--report",
        required=True,
        help="Ficheiro .txt do spectrum_report (AC-106)",
    )
    p_sx.add_argument("--limit", type=int, default=5)
    p_sx.add_argument(
        "--mode", default="hybrid", choices=("fts", "vector", "hybrid")
    )
    p_sx.set_defaults(func=_cmd_analyze_spectrum_explain)
    p_as = an_sub.add_parser("astrometry", help="Medida astrometrica (PO-C01/C02)")
    _add_db_arg(p_as)
    p_as.add_argument("--fits-uri", required=True)
    p_as.add_argument("--x", type=float, required=True)
    p_as.add_argument("--y", type=float, required=True)
    p_as.add_argument("--ra0", type=float, default=None, help="apontamento RA deg")
    p_as.add_argument("--dec0", type=float, default=None, help="apontamento Dec deg")
    p_as.add_argument("--scale-arcsec", type=float, default=None)
    p_as.add_argument("--pa", type=float, default=0.0, help="PA degrees")
    p_as.add_argument("--designation", default=None)
    p_as.add_argument("--band", default="R")
    p_as.add_argument("--nonsidereal", action="store_true")
    p_as.add_argument("--program", default=None)
    p_as.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_as.set_defaults(func=_cmd_analyze_astrometry)
    p_ps = an_sub.add_parser("plate-solve", help="Plate-solve / WCS (AC-110)")
    _add_db_arg(p_ps)
    p_ps.add_argument("--fits-uri", required=True)
    p_ps.add_argument(
        "--backend",
        choices=("auto", "solve-field", "nova", "synthetic"),
        default="auto",
    )
    p_ps.add_argument("--ra-hint", type=float, default=None, help="RA deg (hint)")
    p_ps.add_argument("--dec-hint", type=float, default=None, help="Dec deg (hint)")
    p_ps.add_argument("--radius", type=float, default=None, help="search radius deg")
    p_ps.add_argument("--scale-low", type=float, default=None, help="arcsec/pix")
    p_ps.add_argument("--scale-high", type=float, default=None, help="arcsec/pix")
    p_ps.add_argument("--timeout", type=float, default=120.0)
    p_ps.add_argument("--api-key", default=None, help="nova.astrometry.net")
    p_ps.add_argument("--credentials", default=None)
    p_ps.add_argument(
        "--submit",
        action="store_true",
        help="Nova: envio real (sem dry-run/synthetic)",
    )
    p_ps.add_argument("--program", default=None)
    p_ps.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ps.set_defaults(func=_cmd_analyze_plate_solve)
    p_bl = an_sub.add_parser("blink", help="Blink / diff (PO-C03)")
    _add_db_arg(p_bl)
    p_bl.add_argument("--new-uri", required=True)
    p_bl.add_argument("--ref-uri", required=True)
    p_bl.add_argument("--ra0", type=float, default=None)
    p_bl.add_argument("--dec0", type=float, default=None)
    p_bl.add_argument("--scale-arcsec", type=float, default=None)
    p_bl.add_argument("--pa", type=float, default=0.0)
    p_bl.add_argument("--name", default=None, help="internal name TNS")
    p_bl.add_argument("--program", default=None)
    p_bl.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_bl.set_defaults(func=_cmd_analyze_blink)
    p_su = an_sub.add_parser("sunspots", help="Contagem manchas solares (PO-E03)")
    _add_db_arg(p_su)
    p_su.add_argument("--fits-uri", required=True)
    p_su.add_argument(
        "--filter-confirmed",
        action="store_true",
        required=True,
        help="Confirma filtro solar certificado",
    )
    p_su.add_argument(
        "--no-unfiltered-eyepiece",
        action="store_true",
        required=True,
        help="Confirma que NAO ha ocular sem filtro",
    )
    p_su.add_argument(
        "--daytime-ack",
        action="store_true",
        required=True,
        help="Confirma observacao diurna consciente",
    )
    p_su.add_argument("--filter-name", default="white-light")
    p_su.add_argument("--observer", default="AstroCitizen")
    p_su.add_argument("--k", type=float, default=1.0, help="fator pessoal Wolf")
    p_su.add_argument("--spots", type=int, default=None, help="override manual")
    p_su.add_argument("--groups", type=int, default=None, help="override manual")
    p_su.add_argument("--program", default=None)
    p_su.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_su.set_defaults(func=_cmd_analyze_sunspots)
    p_ex = an_sub.add_parser("export-aavso", help="Export AAVSO Extended")
    _add_db_arg(p_ex)
    p_ex.add_argument("--product", required=True)
    p_ex.add_argument("--star", required=True)
    p_ex.add_argument("--obscode", required=True)
    p_ex.add_argument("--out", required=True)
    p_ex.add_argument("--band", default="V")
    p_ex.set_defaults(func=_cmd_analyze_export_aavso)

    p_wf = sub.add_parser("workflow", help="Workflows P1 (PO-J*/A*/B*/C*/D*/E*)")
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

    p_c = sub.add_parser(
        "contribute", help="Export / submit redes (AAVSO, MPC, TNS, BeSS, ExoClock, IOTA)"
    )
    c_sub = p_c.add_subparsers(dest="contribute_cmd", required=True)

    p_cred = c_sub.add_parser("credentials", help="Credenciais locais de redes")
    cred_sub = p_cred.add_subparsers(dest="cred_cmd", required=True)
    p_cs = cred_sub.add_parser("set", help="Gravar credenciais de uma rede")
    p_cs.add_argument("--credentials", default=None)
    p_cs.add_argument(
        "--network",
        required=True,
        choices=("aavso", "mpc", "tns", "bess", "exoclock", "iota"),
    )
    p_cs.add_argument("--obscode", default=None)
    p_cs.add_argument("--mpc-code", default=None)
    p_cs.add_argument("--email", default=None)
    p_cs.add_argument("--api-key", default=None)
    p_cs.add_argument("--user-id", default=None)
    p_cs.add_argument("--groupid", type=int, default=None)
    p_cs.add_argument("--observer", default=None, help="Nome observador (BeSS/ExoClock/IOTA)")
    p_cs.set_defaults(func=_cmd_contribute_cred_set)
    p_cg = cred_sub.add_parser("show", help="Mostrar credenciais (api_key mascarada)")
    p_cg.add_argument("--credentials", default=None)
    p_cg.add_argument("--network", default=None)
    p_cg.set_defaults(func=_cmd_contribute_cred_show)

    p_cv = c_sub.add_parser(
        "validate", help="Validar produto minimo (AC-141) antes de export"
    )
    _add_db_arg(p_cv)
    p_cv.add_argument(
        "--network",
        required=True,
        choices=("aavso", "mpc", "exoclock", "bess", "tns", "iota", "solar", "wds", "cobs"),
    )
    p_cv.add_argument("--product", default=None)
    p_cv.add_argument("--obscode", default=None)
    p_cv.add_argument("--star", default=None)
    p_cv.add_argument("--designation", default=None)
    p_cv.add_argument("--obs-code", default=None)
    p_cv.add_argument("--ra", type=float, default=None)
    p_cv.add_argument("--dec", type=float, default=None)
    p_cv.add_argument("--epoch", default=None)
    p_cv.add_argument("--target", default=None)
    p_cv.set_defaults(func=_cmd_contribute_validate)

    p_ca = c_sub.add_parser(
        "aavso", help="Export AAVSO Extended + preparar WebObs (oficial)"
    )
    _add_db_arg(p_ca)
    p_ca.add_argument("--product", required=True)
    p_ca.add_argument("--star", required=True)
    p_ca.add_argument("--obscode", default=None)
    p_ca.add_argument("--band", default="V")
    p_ca.add_argument("--chart", default="NA", help="ID carta VSP (default NA)")
    p_ca.add_argument("--out", required=True)
    p_ca.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ca.add_argument("--credentials", default=None)
    p_ca.add_argument(
        "--open-webobs",
        action="store_true",
        help="Abrir WebObs no browser apos gerar AEF",
    )
    p_ca.set_defaults(func=_cmd_contribute_aavso)

    p_cm = c_sub.add_parser("mpc", help="ADES PSV + submit MPC (default dry-run)")
    _add_db_arg(p_cm)
    p_cm.add_argument("--designation", default=None)
    p_cm.add_argument("--obs-code", default=None)
    p_cm.add_argument("--epoch", default=None, help="UTC ISO")
    p_cm.add_argument("--ra", type=float, default=None, help="RA degrees")
    p_cm.add_argument("--dec", type=float, default=None, help="Dec degrees")
    p_cm.add_argument("--mag", type=float, default=None)
    p_cm.add_argument("--band", default="V")
    p_cm.add_argument("--ra-err", type=float, default=0.5)
    p_cm.add_argument("--dec-err", type=float, default=0.5)
    p_cm.add_argument("--obj-type", default="NEO")
    p_cm.add_argument("--email", default=None)
    p_cm.add_argument("--product", default=None, help="Produto astrometry")
    p_cm.add_argument("--out", required=True)
    p_cm.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_cm.add_argument("--credentials", default=None)
    p_cm.add_argument("--submit", action="store_true", help="Envio real (sem dry-run)")
    p_cm.set_defaults(func=_cmd_contribute_mpc)

    p_ct = c_sub.add_parser("tns", help="TNS AT-rep JSON (default sandbox dry-run)")
    _add_db_arg(p_ct)
    p_ct.add_argument("--ra", type=float, default=None)
    p_ct.add_argument("--dec", type=float, default=None)
    p_ct.add_argument("--mag", type=float, default=None)
    p_ct.add_argument("--groupid", type=int, default=None)
    p_ct.add_argument("--reporter", default="AstroCitizen")
    p_ct.add_argument("--filter", default="Clear")
    p_ct.add_argument("--internal-name", default=None)
    p_ct.add_argument("--product", default=None, help="Produto blink_candidate")
    p_ct.add_argument("--api-key", default=None)
    p_ct.add_argument("--user-id", default=None)
    p_ct.add_argument("--out", required=True)
    p_ct.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ct.add_argument("--credentials", default=None)
    p_ct.add_argument("--submit", action="store_true")
    p_ct.add_argument("--prod", action="store_true", help="Usar TNS producao (nao sandbox)")
    p_ct.set_defaults(func=_cmd_contribute_tns)

    p_cb = c_sub.add_parser("bess", help="FITS 1D BeSS (portal manual)")
    _add_db_arg(p_cb)
    p_cb.add_argument("--objname", default="BeStar")
    p_cb.add_argument("--observer", default=None)
    p_cb.add_argument("--date-obs", default="2026-07-21T01:00:00")
    p_cb.add_argument("--exptime", type=float, default=60.0)
    p_cb.add_argument("--wave0", type=float, default=400.0, help="nm")
    p_cb.add_argument("--wave1", type=float, default=700.0, help="nm")
    p_cb.add_argument("--npix", type=int, default=301)
    p_cb.add_argument("--ra", type=float, default=None)
    p_cb.add_argument("--dec", type=float, default=None)
    p_cb.add_argument("--site", default=None)
    p_cb.add_argument("--instrument", default=None)
    p_cb.add_argument("--fits", default=None, help="Anotar FITS 1D existente")
    p_cb.add_argument("--product", default=None, help="Produto spectrum_1d")
    p_cb.add_argument("--out", required=True)
    p_cb.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_cb.add_argument("--credentials", default=None)
    p_cb.set_defaults(func=_cmd_contribute_bess)

    p_ce = c_sub.add_parser("exoclock", help="LC txt ExoClock (upload manual)")
    _add_db_arg(p_ce)
    p_ce.add_argument("--product", required=True)
    p_ce.add_argument("--target", required=True)
    p_ce.add_argument("--telescope", default="AstroCitizen")
    p_ce.add_argument("--observer", default=None)
    p_ce.add_argument("--out", required=True)
    p_ce.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ce.add_argument("--credentials", default=None)
    p_ce.set_defaults(func=_cmd_contribute_exoclock)

    p_ci = c_sub.add_parser("iota", help="Pacote IOTA-ES (hub regional manual)")
    _add_db_arg(p_ci)
    p_ci.add_argument("--event", required=True)
    p_ci.add_argument("--star", required=True)
    p_ci.add_argument("--asteroid", required=True)
    p_ci.add_argument("--observer", default=None)
    p_ci.add_argument("--site", default=None)
    p_ci.add_argument("--result", default="positive", choices=("positive", "negative"))
    p_ci.add_argument("--d-time", default=None)
    p_ci.add_argument("--r-time", default=None)
    p_ci.add_argument("--out", required=True, help="Directorio do pacote")
    p_ci.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ci.add_argument("--credentials", default=None)
    p_ci.set_defaults(func=_cmd_contribute_iota)

    p_csol = c_sub.add_parser("solar", help="Relatorio manchas solares (PO-E03)")
    _add_db_arg(p_csol)
    p_csol.add_argument("--product", required=True)
    p_csol.add_argument("--observer", default=None)
    p_csol.add_argument("--site", default=None)
    p_csol.add_argument("--notes", default=None)
    p_csol.add_argument("--out", required=True)
    p_csol.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_csol.add_argument("--credentials", default=None)
    p_csol.set_defaults(func=_cmd_contribute_solar)

    p_cwds = c_sub.add_parser("wds", help="Export medida WDS / USNO (PO-G01)")
    _add_db_arg(p_cwds)
    p_cwds.add_argument("--product", required=True)
    p_cwds.add_argument("--object", default=None, help="Override WDS / object id")
    p_cwds.add_argument("--observer", default=None)
    p_cwds.add_argument("--observatory", default=None)
    p_cwds.add_argument("--discoverer", default=None)
    p_cwds.add_argument("--notes", default=None)
    p_cwds.add_argument("--no-csv", action="store_true")
    p_cwds.add_argument("--out", required=True)
    p_cwds.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_cwds.add_argument("--credentials", default=None)
    p_cwds.set_defaults(func=_cmd_contribute_wds)

    p_ccobs = c_sub.add_parser("cobs", help="Export COBS/ICQ cometa (PO-A10)")
    _add_db_arg(p_ccobs)
    p_ccobs.add_argument("--product", default=None)
    p_ccobs.add_argument("--designation", default=None)
    p_ccobs.add_argument("--epoch", default=None, help="UTC ISO ou ICQ YYYY MM DD.DD")
    p_ccobs.add_argument("--mag", type=float, default=None)
    p_ccobs.add_argument("--mag-method", dest="mag_method", default=None)
    p_ccobs.add_argument("--comp-cat", dest="comp_cat", default=None)
    p_ccobs.add_argument("--aperture-cm", dest="aperture_cm", type=float, default=None)
    p_ccobs.add_argument("--instr-type", dest="instr_type", default=None)
    p_ccobs.add_argument("--focal-ratio", dest="focal_ratio", type=float, default=None)
    p_ccobs.add_argument(
        "--power-or-exptime", dest="power_or_exptime", type=float, default=None
    )
    p_ccobs.add_argument("--coma-arcmin", dest="coma_arcmin", type=float, default=None)
    p_ccobs.add_argument("--dc", default=None)
    p_ccobs.add_argument("--tail-deg", dest="tail_deg", type=float, default=None)
    p_ccobs.add_argument("--tail-pa", dest="tail_pa", type=float, default=None)
    p_ccobs.add_argument("--obscode", default=None)
    p_ccobs.add_argument("--observer", default=None)
    p_ccobs.add_argument("--location", default=None)
    p_ccobs.add_argument("--notes", default=None)
    p_ccobs.add_argument("--no-csv", action="store_true")
    p_ccobs.add_argument("--out", required=True)
    p_ccobs.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ccobs.add_argument("--credentials", default=None)
    p_ccobs.set_defaults(func=_cmd_contribute_cobs)

    p_cl = c_sub.add_parser("list", help="Listar network_submissions")
    _add_db_arg(p_cl)
    p_cl.add_argument(
        "--network",
        default=None,
        choices=(
            "aavso",
            "mpc",
            "tns",
            "bess",
            "exoclock",
            "iota",
            "solar",
            "wds",
            "cobs",
        ),
    )
    p_cl.set_defaults(func=_cmd_contribute_list)

    p_cfs = c_sub.add_parser(
        "form-schema", help="Mostrar schema de formulario atlas (D-013)"
    )
    p_cfs.add_argument("--network", default=None, help="ex.: aavso")
    p_cfs.add_argument(
        "--list",
        dest="list_networks",
        action="store_true",
        help="Listar redes com schema",
    )
    p_cfs.set_defaults(func=_cmd_contribute_form_schema)

    p_cat = sub.add_parser("catalog", help="Cache institucional / info services (D-013)")
    cat_sub = p_cat.add_subparsers(dest="catalog_cmd", required=True)
    p_cg = cat_sub.add_parser("cache-get", help="Ler entrada do institutional_cache")
    _add_db_arg(p_cg)
    p_cg.add_argument("--provider", required=True, help="ex.: vsx")
    p_cg.add_argument("--id", required=True, help="object_id (nome ou AUID)")
    p_cg.set_defaults(func=_cmd_catalog_cache_get)
    p_clst = cat_sub.add_parser("cache-list", help="Listar cache institucional")
    _add_db_arg(p_clst)
    p_clst.add_argument("--provider", default=None)
    p_clst.add_argument("--limit", type=int, default=50)
    p_clst.set_defaults(func=_cmd_catalog_cache_list)

    p_kb = sub.add_parser("knowledge", help="Base de conhecimento E19 (ingest offline)")
    kb_sub = p_kb.add_subparsers(dest="knowledge_cmd", required=True)
    p_kb_val = kb_sub.add_parser("validate", help="Validar scaffold knowledge-base/")
    p_kb_val.add_argument("--kb-root", default=None)
    p_kb_val.set_defaults(func=_cmd_knowledge_validate)
    p_kb_ing = kb_sub.add_parser(
        "ingest", help="Ingerir fontes T3 (docs/atlas) → chunks + BD"
    )
    _add_db_arg(p_kb_ing)
    p_kb_ing.add_argument("--kb-root", default=None)
    p_kb_ing.add_argument("--source-id", default=None)
    p_kb_ing.add_argument("--tier", default="T3", help="Trust tier (default T3)")
    p_kb_ing.add_argument("--dry-run", action="store_true")
    p_kb_ing.add_argument("--no-db", action="store_true", help="So ficheiros KB")
    p_kb_ing.add_argument("--no-files", action="store_true", help="So SQLite")
    p_kb_ing.add_argument("--corpus-version", default="0.1.0-kb1")
    p_kb_ing.set_defaults(func=_cmd_knowledge_ingest)
    p_kb_idx = kb_sub.add_parser("index", help="Rebuild indice FTS5 (AC-193)")
    _add_db_arg(p_kb_idx)
    p_kb_idx.add_argument("--kb-root", default=None)
    p_kb_idx.add_argument(
        "--no-manifest",
        action="store_true",
        help="Nao actualizar knowledge-base/manifest.json",
    )
    p_kb_idx.set_defaults(func=_cmd_knowledge_index)
    p_kb_se = kb_sub.add_parser(
        "search", help="Pesquisa FTS / vector / hybrid RRF (AC-193…195)"
    )
    _add_db_arg(p_kb_se)
    p_kb_se.add_argument("query", help="Texto livre a pesquisar")
    p_kb_se.add_argument("--limit", type=int, default=10)
    p_kb_se.add_argument("--tier", default=None, help="Filtrar trust_tier (ex. T3)")
    p_kb_se.add_argument("--source-id", default=None)
    p_kb_se.add_argument("--lang", default=None)
    p_kb_se.add_argument("--po-id", default=None)
    p_kb_se.add_argument("--network", default=None)
    p_kb_se.add_argument("--topic", default=None, help="Filtrar topic (JSON topics)")
    p_kb_se.add_argument(
        "--mode",
        default="hybrid",
        choices=("fts", "vector", "hybrid"),
        help="fts | vector | hybrid (RRF; default hybrid)",
    )
    p_kb_se.set_defaults(func=_cmd_knowledge_search)
    p_kb_emb = kb_sub.add_parser(
        "embed", help="Gerar embeddings locais hashing (AC-195)"
    )
    _add_db_arg(p_kb_emb)
    p_kb_emb.add_argument("--kb-root", default=None)
    p_kb_emb.add_argument(
        "--no-manifest",
        action="store_true",
        help="Nao actualizar knowledge-base/manifest.json",
    )
    p_kb_emb.set_defaults(func=_cmd_knowledge_embed)
    p_kb_get = kb_sub.add_parser("get", help="Obter chunk por id (citacao + body)")
    _add_db_arg(p_kb_get)
    p_kb_get.add_argument("chunk_id", help="ex. docs-workflows-002")
    p_kb_get.set_defaults(func=_cmd_knowledge_get)
    p_kb_src = kb_sub.add_parser("sources", help="Listar fontes ingeridas")
    _add_db_arg(p_kb_src)
    p_kb_src.add_argument("--tier", default=None)
    p_kb_src.set_defaults(func=_cmd_knowledge_sources)
    p_kb_ask = kb_sub.add_parser(
        "ask", help="Ajuda grounded: pergunta + citacoes (AC-196, sem LLM)"
    )
    _add_db_arg(p_kb_ask)
    p_kb_ask.add_argument("question", help="Pergunta em texto livre")
    p_kb_ask.add_argument("--limit", type=int, default=5)
    p_kb_ask.add_argument("--tier", default=None)
    p_kb_ask.add_argument("--source-id", default=None)
    p_kb_ask.add_argument("--lang", default=None)
    p_kb_ask.add_argument("--po-id", default=None)
    p_kb_ask.add_argument("--network", default=None)
    p_kb_ask.add_argument("--topic", default=None)
    p_kb_ask.add_argument(
        "--mode",
        default="hybrid",
        choices=("fts", "vector", "hybrid"),
    )
    p_kb_ask.set_defaults(func=_cmd_knowledge_ask)
    p_kb_ev = kb_sub.add_parser(
        "eval-gold", help="Eval citation rate gold-questions (AC-199)"
    )
    _add_db_arg(p_kb_ev)
    p_kb_ev.add_argument("--kb-root", default=None)
    p_kb_ev.add_argument("--limit", type=int, default=5)
    p_kb_ev.add_argument(
        "--mode", default="hybrid", choices=("fts", "vector", "hybrid")
    )
    p_kb_ev.add_argument("--out", default=None, help="Escrever JSON do report")
    p_kb_ev.add_argument("--json", action="store_true", help="Dump JSON no stdout")
    p_kb_ev.set_defaults(func=_cmd_knowledge_eval_gold)
    p_kb_gl = kb_sub.add_parser("glossary", help="Glossario astro/redes/PO (AC-198)")
    gl_sub = p_kb_gl.add_subparsers(dest="glossary_cmd", required=True)
    p_gl_list = gl_sub.add_parser("list", help="Listar / pesquisar termos")
    p_gl_list.add_argument("--kb-root", default=None)
    p_gl_list.add_argument("--query", default=None)
    p_gl_list.add_argument("--limit", type=int, default=50)
    p_gl_list.add_argument("--topic", default=None)
    p_gl_list.add_argument("--network", default=None)
    p_gl_list.add_argument("--po-id", default=None)
    p_gl_list.set_defaults(func=_cmd_knowledge_glossary)
    p_gl_get = gl_sub.add_parser("get", help="Lookup exacto por term/alias")
    p_gl_get.add_argument("term")
    p_gl_get.add_argument("--kb-root", default=None)
    p_gl_get.add_argument("--lang", default=None)
    p_gl_get.set_defaults(func=_cmd_knowledge_glossary)
    p_gl_sync = gl_sub.add_parser("sync", help="Gerar chunks glossary-* em chunks/v1")
    p_gl_sync.add_argument("--kb-root", default=None)
    p_gl_sync.set_defaults(func=_cmd_knowledge_glossary)
    p_kb_mt = kb_sub.add_parser("mcp-tools", help="Listar tools MCP KB (AC-197)")
    p_kb_mt.set_defaults(func=_cmd_knowledge_mcp_tools)
    p_kb_mc = kb_sub.add_parser("mcp-call", help="Invocar tool MCP KB uma vez")
    _add_db_arg(p_kb_mc)
    p_kb_mc.add_argument(
        "tool",
        help="kb_search | kb_get_chunk | kb_list_sources | kb_get_glossary",
    )
    p_kb_mc.add_argument(
        "--arguments",
        default="{}",
        help='JSON object, ex. \'{"query":"AC-106","limit":3}\'',
    )
    p_kb_mc.add_argument("--rate-limit", type=int, default=60)
    p_kb_mc.add_argument("--rate-window", type=float, default=60.0)
    p_kb_mc.set_defaults(func=_cmd_knowledge_mcp_call)
    p_kb_ms = kb_sub.add_parser(
        "mcp-serve", help="Servidor MCP stdio (JSON-RPC linha a linha)"
    )
    _add_db_arg(p_kb_ms)
    p_kb_ms.add_argument("--rate-limit", type=int, default=60)
    p_kb_ms.add_argument("--rate-window", type=float, default=60.0)
    p_kb_ms.set_defaults(func=_cmd_knowledge_mcp_serve)

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
