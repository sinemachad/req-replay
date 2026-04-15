"""Persistent storage for captured requests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from req_replay.models import CapturedRequest, from_dict
from req_replay.filter import FilterCriteria, filter_requests


class RequestStore:
    """File-based store for :class:`CapturedRequest` objects."""

    def __init__(self, base_dir: str | Path = ".req_replay") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request_path(self, request_id: str) -> Path:
        return self.base_dir / f"{request_id}.json"

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, request: CapturedRequest) -> Path:
        """Persist *request* to disk and return its file path."""
        path = self._request_path(request.id)
        path.write_text(json.dumps(request.to_dict(), indent=2), encoding="utf-8")
        return path

    def load(self, request_id: str) -> CapturedRequest:
        """Load a single request by ID.

        Raises
        ------
        FileNotFoundError
            If no request with *request_id* exists in the store.
        """
        path = self._request_path(request_id)
        if not path.exists():
            raise FileNotFoundError(f"No request found with id '{request_id}'")
        data = json.loads(path.read_text(encoding="utf-8"))
        return from_dict(data)

    def delete(self, request_id: str) -> None:
        """Remove a request from the store."""
        path = self._request_path(request_id)
        if not path.exists():
            raise FileNotFoundError(f"No request found with id '{request_id}'")
        path.unlink()

    # ------------------------------------------------------------------
    # Listing & filtering
    # ------------------------------------------------------------------

    def list_all(self) -> List[CapturedRequest]:
        """Return every stored request, sorted by timestamp ascending."""
        requests = []
        for p in sorted(self.base_dir.glob("*.json")):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                requests.append(from_dict(data))
            except Exception:  # noqa: BLE001 – skip corrupt files
                continue
        return requests

    def search(
        self,
        criteria: Optional[FilterCriteria] = None,
    ) -> List[CapturedRequest]:
        """Return stored requests that match *criteria*.

        If *criteria* is ``None`` all requests are returned (same as
        :meth:`list_all`).
        """
        all_requests = self.list_all()
        if criteria is None:
            return all_requests
        return filter_requests(all_requests, criteria)
