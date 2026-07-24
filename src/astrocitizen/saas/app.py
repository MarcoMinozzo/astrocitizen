"""Scaffold SaaS FastAPI (AC-223) — auth simples + /sync/batch + GET observations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from astrocitizen.saas.store import SaasMasterStore

# Token de desenvolvimento (substituir por JWT real em produção)
DEV_TOKEN = os.environ.get("ASTROCITIZEN_SAAS_TOKEN", "dev-token-change-me")


def create_app(store: SaasMasterStore | None = None) -> Any:
    try:
        from fastapi import Depends, FastAPI, Header, HTTPException
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    except ImportError as exc:
        raise ImportError(
            "FastAPI nao instalado. Use: pip install 'astrocitizen[saas]'"
        ) from exc

    db = Path(
        os.environ.get(
            "ASTROCITIZEN_SAAS_DB",
            str(Path.home() / ".local" / "share" / "astrocitizen" / "saas_master.sqlite3"),
        )
    )
    master = store or SaasMasterStore(db)
    security = HTTPBearer(auto_error=False)

    app = FastAPI(title="AstroCitizen SaaS", version="0.0.1")
    app.state.store = master

    def require_auth(
        creds: HTTPAuthorizationCredentials | None = Depends(security),
        authorization: str | None = Header(default=None),
    ) -> str:
        token = None
        if creds is not None:
            token = creds.credentials
        elif authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
        if token != DEV_TOKEN:
            raise HTTPException(status_code=401, detail="unauthorized")
        return token

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/auth/token")
    def auth_token(body: dict[str, Any]) -> dict[str, Any]:
        # Scaffold: aceita qualquer email/password e devolve token de dev
        _ = body.get("email"), body.get("password")
        return {
            "access_token": DEV_TOKEN,
            "refresh_token": DEV_TOKEN,
            "expires_in": 86400,
            "workspace_id": body.get("workspace_id") or "00000000-0000-0000-0000-000000000001",
        }

    @app.post("/sync/batch")
    def sync_batch(
        body: dict[str, Any],
        _auth: str = Depends(require_auth),
    ) -> dict[str, Any]:
        ops = body.get("operations") or []
        if not isinstance(ops, list):
            raise HTTPException(status_code=400, detail="operations deve ser lista")
        results: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        for op in ops:
            if not isinstance(op, dict):
                continue
            row = master.apply_operation(op)
            if row.get("status") == "conflict":
                conflicts.append(row)
            else:
                results.append(row)
        return {"results": results, "conflicts": conflicts}

    @app.get("/observations")
    def get_observations(
        workspace_id: str | None = None,
        limit: int = 100,
        _auth: str = Depends(require_auth),
        x_workspace_id: str | None = Header(default=None, alias="X-Workspace-Id"),
    ) -> dict[str, Any]:
        ws = workspace_id or x_workspace_id
        items = master.list_observations(workspace_id=ws, limit=limit)
        return {"items": items, "count": len(items)}

    return app


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    import uvicorn

    app = create_app()
    uvicorn.run(app, host=host, port=port)
