"""Group captured requests into named collections."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from req_replay.models import CapturedRequest
from req_replay.storage import RequestStore


@dataclass
class RequestGroup:
    name: str
    request_ids: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "request_ids": self.request_ids,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RequestGroup":
        return cls(
            name=data["name"],
            request_ids=data.get("request_ids", []),
            description=data.get("description", ""),
        )


def create_group(store: RequestStore, name: str, description: str = "") -> RequestGroup:
    """Create a new empty group and persist it."""
    group = RequestGroup(name=name, description=description)
    _save_group(store, group)
    return group


def add_to_group(store: RequestStore, name: str, request_id: str) -> RequestGroup:
    """Add a request ID to a named group."""
    group = get_group(store, name)
    if request_id not in group.request_ids:
        group.request_ids.append(request_id)
    _save_group(store, group)
    return group


def remove_from_group(store: RequestStore, name: str, request_id: str) -> RequestGroup:
    """Remove a request ID from a named group."""
    group = get_group(store, name)
    group.request_ids = [rid for rid in group.request_ids if rid != request_id]
    _save_group(store, group)
    return group


def get_group(store: RequestStore, name: str) -> RequestGroup:
    """Load a group by name; raises KeyError if not found."""
    path = _group_path(store, name)
    if not path.exists():
        raise KeyError(f"Group '{name}' not found.")
    import json
    data = json.loads(path.read_text())
    return RequestGroup.from_dict(data)


def list_groups(store: RequestStore) -> List[str]:
    """Return names of all persisted groups."""
    groups_dir = store.base_path / "groups"
    if not groups_dir.exists():
        return []
    return [p.stem for p in sorted(groups_dir.glob("*.json"))]


def resolve_group(store: RequestStore, name: str) -> List[CapturedRequest]:
    """Return the CapturedRequest objects for every ID in the group."""
    group = get_group(store, name)
    requests = []
    for rid in group.request_ids:
        try:
            requests.append(store.load(rid))
        except FileNotFoundError:
            pass
    return requests


def _save_group(store: RequestStore, group: RequestGroup) -> None:
    import json
    path = _group_path(store, group.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(group.to_dict(), indent=2))


def _group_path(store: RequestStore, name: str):
    return store.base_path / "groups" / f"{name}.json"
