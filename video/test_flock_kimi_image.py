#!/usr/bin/env python3
"""
Real test: call FLock API with Kimi (multimodal) using an image.
Uses the KrumpGotchi avatar as the image input.

Setup:
  FLOCK_API_KEY must be from the API Platform (platform.flock.io), NOT from train.flock.io.
  At https://platform.flock.io: create a team → create API key → add credits (Billing).
  export FLOCK_API_KEY="sk-..."
  export FLOCK_KIMI_MODEL="kimi-k2.5"   # or exact model id from FLock marketplace

Run from repo root:
  .venv-video/bin/python video/test_flock_kimi_image.py

Or with .env (script loads REPO_ROOT/.env for FLOCK_* vars).
"""
import base64
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

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

FLOCK_API_KEY = os.environ.get("FLOCK_API_KEY")
FLOCK_KIMI_MODEL = os.environ.get("FLOCK_KIMI_MODEL", "kimi-k2.5")
AVATAR_PATH = REPO_ROOT / "docs" / "krumpgotchi-assets" / "krumpgotchi-avatar.png"
FLOCK_URL = "https://api.flock.io/v1/chat/completions"


def main() -> int:
    if not FLOCK_API_KEY:
        print("Set FLOCK_API_KEY (from https://platform.flock.io).", file=sys.stderr)
        return 1
    if not AVATAR_PATH.exists():
        print(f"Avatar not found: {AVATAR_PATH}", file=sys.stderr)
        return 1

    with open(AVATAR_PATH, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")

    # OpenAI-compatible multimodal message: text + image
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in one or two sentences. It is the KrumpGotchi mascot for a rehab app. What do you see?",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
            ],
        }
    ]

    payload = {
        "model": FLOCK_KIMI_MODEL,
        "messages": messages,
        "max_tokens": 1024,  # API default is 16; need more for image description + reasoning
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-litellm-api-key": FLOCK_API_KEY,
    }

    try:
        import httpx
    except ImportError:
        print("Install httpx: pip install httpx", file=sys.stderr)
        return 1

    print(f"Calling FLock API (model={FLOCK_KIMI_MODEL}) with KrumpGotchi avatar image...")
    resp = httpx.post(FLOCK_URL, headers=headers, json=payload, timeout=60.0)

    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {resp.text}", file=sys.stderr)
        if resp.status_code == 401:
            print(
                "\n401 = wrong API key for this endpoint. Use a key from platform.flock.io (API Platform),\n"
                "not from train.flock.io. Create key: https://platform.flock.io → Team → API key; add credits in Billing.",
                file=sys.stderr,
            )
        return 1

    data = resp.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    content = (message.get("content") or "").strip()
    reasoning = (message.get("reasoning_content") or "").strip()
    print("Kimi reply:")
    if content:
        print(content)
    if reasoning:
        if content:
            print("\n--- Reasoning ---\n")
        print(reasoning)
    if not content and not reasoning:
        print("(empty)")
        print("Raw response (for debugging):", json.dumps(data, indent=2)[:1500], file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
