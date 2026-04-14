"""Storage layer for persisting captured requests to disk."""

import json
import os
from pathlib import Path
from typing import List, Optional

from req_replay.models import CapturedRequest

DEFAULT_STORE_DIR = Path.home() / ".req-replay" / "captures"


class RequestStore:
    """Manages persistence of captured HTTP requests."""

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = Path(store_dir) if store_dir else DEFAULT_STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _request_path(self, request_id: str) -> Path:
        return self.store_dir / f"{request_id}.json"

    def save(self, request: CapturedRequest) -> Path:
        """Persist a captured request to disk."""
        path = self._request_path(request.id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(request.to_dict(), f, indent=2)
        return path

    def load(self, request_id: str) -> CapturedRequest:
        """Load a captured request by ID."""
        path = self._request_path(request_id)
        if not path.exists():
            raise FileNotFoundError(f"No captured request found with id: {request_id}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CapturedRequest.from_dict(data)

    def list_all(self) -> List[CapturedRequest]:
        """Return all stored captured requests sorted by capture time."""
        requests = []
        for file in self.store_dir.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            requests.append(CapturedRequest.from_dict(data))
        return sorted(requests, key=lambda r: r.captured_at)

    def delete(self, request_id: str) -> bool:
        """Delete a stored request by ID. Returns True if deleted."""
        path = self._request_path(request_id)
        if path.exists():
            os.remove(path)
            return True
        return False

    def clear(self) -> int:
        """Delete all stored requests. Returns count of deleted files."""
        count = 0
        for file in self.store_dir.glob("*.json"):
            os.remove(file)
            count += 1
        return count
