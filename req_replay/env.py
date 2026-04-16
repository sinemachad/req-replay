"""Environment profile management for req-replay."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class EnvProfile:
    name: str
    variables: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"name": self.name, "variables": self.variables}

    @classmethod
    def from_dict(cls, data: dict) -> "EnvProfile":
        return cls(name=data["name"], variables=data.get("variables", {}))

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.variables.get(key, default)


def _profile_path(base_dir: Path, name: str) -> Path:
    return base_dir / "envs" / f"{name}.json"


def save_profile(base_dir: Path, profile: EnvProfile) -> Path:
    path = _profile_path(base_dir, profile.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile.to_dict(), indent=2))
    return path


def load_profile(base_dir: Path, name: str) -> EnvProfile:
    path = _profile_path(base_dir, name)
    if not path.exists():
        raise FileNotFoundError(f"Environment profile '{name}' not found.")
    return EnvProfile.from_dict(json.loads(path.read_text()))


def list_profiles(base_dir: Path) -> list[str]:
    env_dir = base_dir / "envs"
    if not env_dir.exists():
        return []
    return sorted(p.stem for p in env_dir.glob("*.json"))


def delete_profile(base_dir: Path, name: str) -> None:
    path = _profile_path(base_dir, name)
    if not path.exists():
        raise FileNotFoundError(f"Environment profile '{name}' not found.")
    path.unlink()


def apply_profile(url: str, headers: Dict[str, str], profile: EnvProfile) -> tuple[str, Dict[str, str]]:
    """Substitute {{VAR}} placeholders in url and header values."""
    for key, value in profile.variables.items():
        placeholder = f"{{{{{key}}}}}"
        url = url.replace(placeholder, value)
        headers = {k: v.replace(placeholder, value) for k, v in headers.items()}
    return url, headers
