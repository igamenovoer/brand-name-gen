"""
Configuration loader for uniqueness evaluation.

Precedence:
1) brand-name-gen-config.yaml in current working directory
2) BRAND_NAME_GEN_CONFIG environment variable (path to YAML)
3) Defaults from Defaults class
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from ruamel.yaml import YAML

from .defaults import Defaults
from .types import UniquenessConfig


def _read_yaml(path: str) -> Dict[str, Any]:
    yaml = YAML(typ="safe")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f) or {}
    if not isinstance(data, dict):
        return {}
    return data  # type: ignore[return-value]


def _resolve_config_path() -> Optional[str]:
    pwd_cfg = os.path.join(os.getcwd(), "brand-name-gen-config.yaml")
    if os.path.isfile(pwd_cfg):
        return pwd_cfg
    env_path = os.getenv("BRAND_NAME_GEN_CONFIG")
    if env_path and os.path.isfile(env_path):
        return env_path
    return None


def load_uniqueness_config(*, overrides: Optional[Dict[str, Any]] = None) -> UniquenessConfig:
    """Load UniquenessConfig with YAML precedence and optional overrides.

    Parameters
    ----------
    overrides : dict, optional
        Key-value pairs to override final config (e.g., matcher_engine)
    """

    cfg_dict: Dict[str, Any] = {
        "matcher_engine": Defaults.MATCHER_ENGINE,
        "weights": dict(Defaults.WEIGHTS),
        "thresholds": dict(Defaults.THRESHOLDS),
    }

    path = _resolve_config_path()
    if path:
        data = _read_yaml(path)
        # Only copy recognized keys
        if isinstance(data.get("matcher_engine"), str):
            cfg_dict["matcher_engine"] = data["matcher_engine"]
        if isinstance(data.get("weights"), dict):
            cfg_dict["weights"].update({k: int(v) for k, v in data["weights"].items() if isinstance(v, (int, float))})
        if isinstance(data.get("thresholds"), dict):
            cfg_dict["thresholds"].update({k: int(v) for k, v in data["thresholds"].items() if isinstance(v, (int, float))})

    if overrides:
        cfg_dict.update(overrides)

    return UniquenessConfig(**cfg_dict)

