"""Behave environment configuration."""

import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def before_all(context):
    """Set up shared test configuration."""
    from app.config import settings
    settings.database_url = "sqlite:///./test_agente_soc.db"
    settings.correlation_window_seconds = 3600
    settings.brute_force_threshold = 3
    settings.telegram_bot_token = ""
    settings.telegram_chat_ids = ""


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    try:
        from app.config import settings
    except Exception:
        return
    _orig_map = {
        '_orig_token': 'telegram_bot_token',
        '_orig_chats': 'telegram_chat_ids',
        '_orig_window': 'correlation_window_seconds',
        '_orig_threshold': 'brute_force_threshold',
    }
    for ctx_attr, settings_attr in _orig_map.items():
        try:
            val = getattr(context, ctx_attr, None)
            if val is not None:
                setattr(settings, settings_attr, val)
        except Exception:
            pass

    # Strip cross-scenario state that can pollute later scenarios
    # NOTE: behave Context overrides __delattr__ in a way that does NOT
    # reliably delete attributes. We must reach into __dict__ directly.
    # See: behave/model.py (Context.__delattr__ uses _stack which may
    # not remove from the active frame).
    for stale in ['_matched_pattern', 'anomalies', 'server_alerts', 'incident_result',
                  'notification_result', 'skill', 'server_skill', 'patterns', 'events']:
        if stale in context.__dict__:
            del context.__dict__[stale]

    # Strip cross-scenario state that can pollute later scenarios
    for stale in ['_matched_pattern', 'anomalies', 'server_alerts', 'incident_result',
                  'notification_result', 'skill', 'server_skill', 'patterns', 'events', 'servers']:
        try:
            delattr(context, stale)
        except Exception:
            pass
