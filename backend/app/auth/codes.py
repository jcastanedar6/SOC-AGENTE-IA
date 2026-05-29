import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

SESSION_TTL_MINUTES = 5
CLEANUP_INTERVAL = 60

_sessions: dict[str, dict] = {}
_last_cleanup: float = 0


def _cleanup():
    now = datetime.now(timezone.utc)
    expired = [sid for sid, s in _sessions.items() if s["expires_at"] < now]
    for sid in expired:
        del _sessions[sid]


def _auto_cleanup():
    import time
    global _last_cleanup
    now = time.monotonic()
    if now - _last_cleanup > CLEANUP_INTERVAL:
        _cleanup()
        _last_cleanup = now


def create_session(phone: str) -> tuple[str, str]:
    _auto_cleanup()
    session_id = secrets.token_urlsafe(24)
    code = str(secrets.randbelow(900000) + 100000)
    _sessions[session_id] = {
        "phone": phone,
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=SESSION_TTL_MINUTES),
    }
    return session_id, code


def verify_code(session_id: str, code: str) -> Optional[str]:
    session = _sessions.get(session_id)
    if not session:
        return None
    if session["expires_at"] < datetime.now(timezone.utc):
        del _sessions[session_id]
        return None
    if session["code"] != code:
        return None
    phone = session["phone"]
    del _sessions[session_id]
    return phone
