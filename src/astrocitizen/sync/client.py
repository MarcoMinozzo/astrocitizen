"""Cliente HTTP push /sync/batch (AC-222)."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from astrocitizen.shared.errors import DomainError
from astrocitizen.shared.timeutil import utc_now_iso
from astrocitizen.sync.canonical import batch_operation


class SyncClient:
    """Push de operações pending da sync_queue para o SaaS."""

    def __init__(
        self,
        archive: Any,
        *,
        base_url: str,
        token: str,
        device_id: str | None = None,
        workspace_id: UUID | None = None,
        opener: Any | None = None,
        timeout_s: float = 60.0,
    ) -> None:
        self.archive = archive
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.device_id = device_id or "desktop-local"
        self.workspace_id = workspace_id
        self._opener = opener
        self.timeout_s = timeout_s

    def push_pending(self, *, limit: int = 50) -> dict[str, Any]:
        items = self.archive.list_sync_queue(status="pending", limit=limit)
        if not items:
            return {"pushed": 0, "results": [], "conflicts": []}

        ops = [
            batch_operation(
                client_op_id=it.client_op_id,
                entity=it.entity_type,
                operation=it.operation,
                payload=it.payload,
                client_timestamp_utc=it.created_at or utc_now_iso(),
            )
            for it in items
        ]
        body = {
            "device_id": self.device_id,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "operations": ops,
        }
        for it in items:
            self.archive.update_sync_status(it.id, status="in_flight")

        try:
            response = self._post_json("/sync/batch", body)
        except DomainError as exc:
            for it in items:
                self.archive.update_sync_status(
                    it.id, status="failed", last_error=str(exc)
                )
            raise

        results = response.get("results") or []
        conflicts = response.get("conflicts") or []
        by_op = {str(r.get("client_op_id")): r for r in results}
        for c in conflicts:
            by_op[str(c.get("client_op_id"))] = {**c, "status": "conflict"}

        for it in items:
            key = str(it.client_op_id)
            row = by_op.get(key)
            if row is None:
                self.archive.update_sync_status(
                    it.id, status="failed", last_error="sem resposta para client_op_id"
                )
                continue
            status = str(row.get("status") or "failed")
            if status == "accepted":
                self.archive.update_sync_status(
                    it.id,
                    status="acked",
                    server_id=str(row.get("server_id") or "") or None,
                    acked=True,
                )
            elif status == "conflict":
                self.archive.update_sync_status(
                    it.id,
                    status="conflict",
                    last_error=str(row.get("reason") or "conflict"),
                )
            else:
                self.archive.update_sync_status(
                    it.id,
                    status="failed",
                    last_error=str(row.get("reason") or status),
                )
        return {
            "pushed": len(items),
            "results": results,
            "conflicts": conflicts,
        }

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "AstroCitizen/0.0.1 (SyncClient)",
            "X-Device-Id": self.device_id,
        }
        if self.workspace_id is not None:
            headers["X-Workspace-Id"] = str(self.workspace_id)
        if self._opener is not None:
            raw = self._opener(url, data, headers)
            return json.loads(raw) if isinstance(raw, str) else raw
        req = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=self.timeout_s) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise DomainError(
                f"sync HTTP {exc.code}: {detail[:200]}", rule_id="AC-222"
            ) from exc
        except URLError as exc:
            raise DomainError(
                f"sync rede indisponivel: {exc.reason}", rule_id="AC-222"
            ) from exc
