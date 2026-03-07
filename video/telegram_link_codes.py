"""
One-time link codes for "Link Telegram" flow: website verifies code to associate
a Telegram user with a web account. Codes expire after 5 minutes.
"""
import json
import os
import random
import string
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CODES_FILE = REPO_ROOT / "data" / "telegram_link_codes.json"
EXPIRY_SECONDS = 300  # 5 minutes


def _ensure_dir() -> None:
    CODES_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    _ensure_dir()
    if not CODES_FILE.exists():
        return {"codes": {}}
    try:
        with open(CODES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"codes": {}}


def _save(data: dict) -> None:
    _ensure_dir()
    with open(CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _generate_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_code(telegram_id: int, chat_id: int, username: str | None) -> str:
    """Create a one-time link code for this Telegram user. Returns the code."""
    data = _load()
    # Expire old codes
    now = time.time()
    codes = {
        k: v
        for k, v in data.get("codes", {}).items()
        if v.get("expires_at", 0) > now
    }
    code = _generate_code()
    while code in codes:
        code = _generate_code()
    codes[code] = {
        "telegram_id": telegram_id,
        "chat_id": chat_id,
        "username": username or "",
        "expires_at": now + EXPIRY_SECONDS,
    }
    data["codes"] = codes
    _save(data)
    return code


def verify_and_consume_code(code: str) -> dict | None:
    """
    If code is valid and not expired, return {telegram_id, telegram_username} and
    remove the code. Otherwise return None.
    """
    if not code or len(code) != 6:
        return None
    code = code.strip().upper()
    data = _load()
    codes = data.get("codes", {})
    entry = codes.get(code)
    if not entry:
        return None
    now = time.time()
    if entry.get("expires_at", 0) <= now:
        del codes[code]
        data["codes"] = codes
        _save(data)
        return None
    result = {
        "telegram_id": entry["telegram_id"],
        "telegram_username": entry.get("username") or "",
    }
    del codes[code]
    data["codes"] = codes
    _save(data)
    return result
