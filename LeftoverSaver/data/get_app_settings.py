import json
import os

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'app_settings.json')

def get_ai_models():
    """Return a list of AI models from app_settings.json."""
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Collect all keys that start with 'ai_model'
            return [v for k, v in data.items() if k.startswith('ai_model')]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_other_settings():
    """Return a list of remaining settings (not AI models) from app_settings.json."""
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [{"name": k, "value": v} for k, v in data.items() if not k.startswith('ai_model')]
    except (FileNotFoundError, json.JSONDecodeError):
        return []