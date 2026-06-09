"""YAML code definition loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from jpclaims.exceptions import ConfigurationError


def load_code_definitions(path: str | Path) -> dict[str, Any]:
    """Load diagnosis/medication/procedure/cooccurrence definitions from YAML."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Definition file not found: {p}")
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ConfigurationError("Code definitions must be a mapping at top level")
    for key in ("diagnosis_groups", "medication_groups", "procedure_groups", "cooccurrence_groups"):
        data.setdefault(key, {})
    data.setdefault("composite_features", {})
    data.setdefault("exclusive_groups", {})
    data.setdefault("comorbidity_groups", {})
    data["_definition_hash"] = definition_hash(data)
    return data


def definition_hash(data: dict[str, Any]) -> str:
    """Stable hash of code definitions for QC reproducibility."""
    payload = {k: v for k, v in data.items() if not k.startswith("_")}
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
