import os
from pathlib import Path
from typing import Any, Dict
import yaml

_CONFIG_CACHE: Dict[str, Any] | None = None

class ConfigError(Exception):
    pass

def load_config() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    config_path = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    if not config_path.exists():
        raise ConfigError(f"Config file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Override with env variables if present
    providers = data.get("providers", {})
    google = providers.get("google", {})

    # Generic override helper
    def override(path: str, env_var: str):
        parts = path.split('.')
        ref = data
        for p in parts[:-1]:
            ref = ref.setdefault(p, {})
        if env_var in os.environ and os.environ[env_var]:
            ref[parts[-1]] = os.environ[env_var]

    override("providers.google.generative_ai.api_key", "GOOGLE_GEMINI_API_KEY")
    override("providers.google.generative_ai.model", "GOOGLE_GEMINI_MODEL")
    override("providers.google.places.api_key", "GOOGLE_PLACES_API_KEY")

    _CONFIG_CACHE = data
    return data

def get_setting(path: str, default: Any | None = None) -> Any:
    cfg = load_config()
    parts = path.split('.')
    ref: Any = cfg
    for p in parts:
        if isinstance(ref, dict) and p in ref:
            ref = ref[p]
        else:
            return default
    return ref
