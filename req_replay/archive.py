"""Archive and restore captured requests to/from a zip bundle."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import List

from req_replay.models import CapturedRequest, from_dict as request_from_dict
from req_replay.storage import RequestStore


def export_archive(store: RequestStore, dest: Path) -> List[str]:
    """Write all stored requests to a zip archive.

    Each request is stored as ``<id>.json`` inside the zip.
    Returns the list of request IDs that were archived.
    """
    ids = store.list_ids()
    dest.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for req_id in ids:
            req = store.load(req_id)
            payload = json.dumps(req.to_dict(), indent=2)
            zf.writestr(f"{req_id}.json", payload)

    return ids


def import_archive(
    archive: Path,
    store: RequestStore,
    overwrite: bool = False,
) -> List[str]:
    """Load requests from a zip archive into *store*.

    Parameters
    ----------
    archive:
        Path to the ``.zip`` file produced by :func:`export_archive`.
    store:
        Destination store.
    overwrite:
        When *True* existing entries are replaced; when *False* they are
        skipped silently.

    Returns the list of request IDs that were imported (skipped IDs are
    excluded).
    """
    if not archive.exists():
        raise FileNotFoundError(f"Archive not found: {archive}")

    existing = set(store.list_ids())
    imported: List[str] = []

    with zipfile.ZipFile(archive, "r") as zf:
        for name in zf.namelist():
            if not name.endswith(".json"):
                continue
            req_id = name[: -len(".json")]
            if req_id in existing and not overwrite:
                continue
            data = json.loads(zf.read(name))
            req: CapturedRequest = request_from_dict(data)
            store.save(req)
            imported.append(req_id)

    return imported
