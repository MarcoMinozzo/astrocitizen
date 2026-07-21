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
    CountSunspots,
    ExtractSpectrum1D,
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


def _cmd_analyze_spectrum(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    store = LocalArtifactStore(Path(args.artifacts))
    product = ExtractSpectrum1D(archive, store).execute(
        workspace_id=ws.id,
        fits_uri=args.fits_uri,
        trace_y=args.trace_y,
        half_width=args.half_width,
        axis=args.axis,
        wave0_nm=args.wave0,
        wave1_nm=args.wave1,
        pix_a=args.pix_a,
        wave_a_nm=args.wave_a,
        pix_b=args.pix_b,
        wave_b_nm=args.wave_b,
        program_id=UUID(args.program) if args.program else None,
        objname=args.objname,
    )
    print(
        f"product={product.id}\ttype={product.product_type}\t"
        f"wave={product.summary.get('wave0_nm')}-{product.summary.get('wave1_nm')}nm\t"
        f"uri={product.parameters.get('spectrum_uri')}"
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


def _cmd_contribute_aavso(args: argparse.Namespace) -> int:
    archive = _open_archive(Path(args.db))
    ws = _ensure_default_workspace(archive)
    cred = LocalCredentialsStore(Path(args.credentials) if args.credentials else None)
    obscode = args.obscode or cred.get_network("aavso").get("obscode")
    if not obscode:
        print("falta --obscode ou credentials aavso.obscode")
        archive.close()
        return 1
    out = Path(args.out)
    ExportAavso(archive).execute(
        product_id=UUID(args.product),
        star_name=args.star,
        observer_code=str(obscode),
        out_path=out,
        band=args.band,
    )
    store = LocalArtifactStore(Path(args.artifacts))
    uri = store.put(out, key=f"export/aavso/{out.name}")
    sub = NetworkSubmission(
        id=new_id(),
        workspace_id=ws.id,
        network="aavso",
        status="draft",
        artifact_uri=uri,
        product_id=UUID(args.product),
        payload_summary={"star": args.star, "obscode": obscode, "note": "upload via WebObs"},
    )
    archive.save_network_submission(sub)
    print(f"wrote={out}\turi={uri}\tsubmission={sub.id}\twebobs=https://www.aavso.org/webobs/")
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
    p_sp = an_sub.add_parser("spectrum", help="Extracao espectro 1D (PO-B01)")
    _add_db_arg(p_sp)
    p_sp.add_argument("--fits-uri", required=True)
    p_sp.add_argument("--trace-y", type=float, required=True)
    p_sp.add_argument("--half-width", type=int, default=3)
    p_sp.add_argument("--axis", choices=("x", "y"), default="x")
    p_sp.add_argument("--wave0", type=float, default=None, help="nm")
    p_sp.add_argument("--wave1", type=float, default=None, help="nm")
    p_sp.add_argument("--pix-a", type=float, default=None)
    p_sp.add_argument("--wave-a", type=float, default=None, help="nm")
    p_sp.add_argument("--pix-b", type=float, default=None)
    p_sp.add_argument("--wave-b", type=float, default=None, help="nm")
    p_sp.add_argument("--objname", default=None)
    p_sp.add_argument("--program", default=None)
    p_sp.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_sp.set_defaults(func=_cmd_analyze_spectrum)
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

    p_ca = c_sub.add_parser("aavso", help="Export AAVSO Extended (WebObs manual)")
    _add_db_arg(p_ca)
    p_ca.add_argument("--product", required=True)
    p_ca.add_argument("--star", required=True)
    p_ca.add_argument("--obscode", default=None)
    p_ca.add_argument("--band", default="V")
    p_ca.add_argument("--out", required=True)
    p_ca.add_argument("--artifacts", default=str(default_artifacts_root()))
    p_ca.add_argument("--credentials", default=None)
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

    p_cl = c_sub.add_parser("list", help="Listar network_submissions")
    _add_db_arg(p_cl)
    p_cl.add_argument(
        "--network",
        default=None,
        choices=("aavso", "mpc", "tns", "bess", "exoclock", "iota", "solar"),
    )
    p_cl.set_defaults(func=_cmd_contribute_list)

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
