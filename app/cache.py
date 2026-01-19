from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict

from app.schema import ClusterConfig


def canonicalize_config(config: ClusterConfig) -> Dict:
    """
    Produce a stable, JSON-serializable dict for hashing.

    Notes:
    - Uses pydantic's model_dump for deterministic output.
    - Excludes defaults_applied because it is informational.
    """
    data = config.model_dump(mode="json")
    data.pop("defaults_applied", None)
    return data


def hash_config(config: ClusterConfig) -> str:
    payload = canonicalize_config(config)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def glb_path_for_hash(hash_value: str, base_dir: Path) -> Path:
    return base_dir / f"{hash_value}.glb"


def glb_exists(hash_value: str, base_dir: Path) -> bool:
    return glb_path_for_hash(hash_value, base_dir).exists()


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
