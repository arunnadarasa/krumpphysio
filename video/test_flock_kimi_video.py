#!/usr/bin/env python3
"""
Real test: call FLock API with Kimi (multimodal) using a video.
Uses video/samples/test_video.mp4 by default.

Setup: same as test_flock_kimi_image.py (FLOCK_API_KEY from platform.flock.io).
Override video path: VIDEO_PATH=/path/to/short.mp4

Run from repo root:
  .venv-video/bin/python video/test_flock_kimi_video.py
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
VIDEO_PATH = Path(os.environ.get("VIDEO_PATH", REPO_ROOT / "video" / "samples" / "test_video.mp4"))
if not VIDEO_PATH.is_absolute():
    VIDEO_PATH = REPO_ROOT / VIDEO_PATH
FLOCK_URL = "https://api.flock.io/v1/chat/completions"


def main() -> int:
    if not FLOCK_API_KEY:
        print("Set FLOCK_API_KEY (from https://platform.flock.io).", file=sys.stderr)
        return 1
    if not VIDEO_PATH.exists():
        print(f"Video not found: {VIDEO_PATH}", file=sys.stderr)
        return 1

    with open(VIDEO_PATH, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")

    size_mb = len(b64) * 3 / 4 / (1024 * 1024)
    print(f"Video size: {size_mb:.2f} MB (base64)", file=sys.stderr)

    # OpenAI-style multimodal: text + video (video_url with data URL)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Watch this short video. In 1–2 sentences, what is the person doing?",
                },
                {
                    "type": "video_url",
                    "video_url": {"url": f"data:video/mp4;base64,{b64}"},
                },
            ],
        }
    ]

    payload = {
        "model": FLOCK_KIMI_MODEL,
        "messages": messages,
        "max_tokens": 1024,
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

    print(f"Calling FLock API (model={FLOCK_KIMI_MODEL}) with video...")
    resp = httpx.post(FLOCK_URL, headers=headers, json=payload, timeout=120.0)

    if resp.status_code != 200:
        print(f"API error {resp.status_code}: {resp.text}", file=sys.stderr)
        if resp.status_code == 401:
            print(
                "\n401 = wrong API key. Use a key from platform.flock.io (API Platform).",
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
