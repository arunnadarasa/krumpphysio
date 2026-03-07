#!/usr/bin/env python3
"""
Small API for the KrumpGotchi website to verify Telegram link codes.
Run with: .venv-video/bin/python video/link_api.py
Set LINK_API_PORT (default 8765) and ensure the website can reach this URL (e.g. ngrok for local).
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Load .env if present
_env = REPO_ROOT / ".env"
if _env.exists():
    with open(_env, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip("'\"")
                if k:
                    os.environ.setdefault(k, v)

from flask import Flask, jsonify, request
from flask_cors import CORS

from video.telegram_link_codes import verify_and_consume_code

app = Flask(__name__)

# CORS so the Lovable app can call this API from the browser (handles preflight OPTIONS)
CORS_ORIGINS = os.environ.get(
    "LINK_CORS_ORIGINS",
    "https://krumpgotchi.lovable.app,http://localhost:3000,http://localhost:5173",
).strip().split(",")
CORS(app, origins=[o.strip() for o in CORS_ORIGINS if o.strip()])


@app.route("/api/link/verify", methods=["GET"])
def verify():
    """
    GET /api/link/verify?code=XXXXXX
    Returns 200 { "telegram_id": 123, "telegram_username": "joe" } or 404 if invalid/expired.
    """
    code = request.args.get("code", "").strip()
    result = verify_and_consume_code(code)
    if not result:
        return jsonify({"error": "Invalid or expired code"}), 404
    return jsonify(result)


@app.route("/api/link/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("LINK_API_PORT", "8765"))
    app.run(host="0.0.0.0", port=port, debug=False)
