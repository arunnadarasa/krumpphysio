#!/usr/bin/env python3
"""
KrumpPhysio Video Bot (Telegram sidecar)

Purpose:
- Receive short rehab/krump clips directly in Telegram
- Download them to the KrumpPhysio repo
- Run the local MediaPipe analysis script
- Reply with a KrumpPhysio-style summary (no LLM required)

This bot is intentionally simple and runs *alongside* OpenClaw. For the hackathon
you can show real "upload video on Telegram → get scored feedback" even if
OpenClaw's own Telegram plugin doesn't yet stream video files to the agent.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Tuple, Optional

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
VIDEO_DIR = REPO_ROOT / "video" / "telegram"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# Path to the video venv Python and analysis script
VIDEO_PYTHON = REPO_ROOT / ".venv-video" / "bin" / "python"
ANALYSIS_SCRIPT = REPO_ROOT / "video" / "analyse_movement.py"

VALID_JOINTS = {
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
}


def parse_caption(caption: Optional[str]) -> Optional[Tuple[str, float]]:
    """
    Parse joint + target from caption.

    Accepted formats (case-insensitive):
    - "/analyze left_knee 90"
    - "/analyse right_shoulder 120"
    - "left_knee 90"
    """
    if not caption:
        return None

    text = caption.strip().lower()
    # Strip optional command prefix
    if text.startswith("/analyze"):
        text = text[len("/analyze") :].strip()
    elif text.startswith("/analyse"):
        text = text[len("/analyse") :].strip()

    parts = text.split()
    if len(parts) < 2:
        return None

    joint, target_str = parts[0], parts[1]
    if joint not in VALID_JOINTS:
        return None

    try:
        target = float(target_str)
    except ValueError:
        return None

    return joint, target


def run_analysis(video_path: Path, joint: str, target: float) -> dict:
    """Run the local analyse_movement.py script and return parsed JSON."""
    cmd = [
        str(VIDEO_PYTHON),
        str(ANALYSIS_SCRIPT),
        "--video",
        str(video_path),
        "--joint",
        joint,
        "--target",
        str(target),
        "--extended",
    ]

    result = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Analysis script failed (code={result.returncode}): {result.stderr.strip()}"
        )

    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse analysis output as JSON: {exc}") from exc


def build_reply_from_analysis(data: dict, joint: str, target: float) -> str:
    """Convert analysis JSON into a KrumpPhysio-style text summary."""
    summary = data.get("summary") or []
    meta = data.get("meta") or {}

    if not summary:
        return "I couldn't detect a clear pose in that clip. Try a shorter, clearer video focusing on one joint."

    item = summary[0]
    observed = float(item.get("observed", target))
    smoothness = meta.get("smoothness", "unknown")

    # Very simple scoring heuristic based on angle error
    diff = abs(observed - target)
    if diff <= 5:
        score = 10
        quality = "excellent alignment"
    elif diff <= 15:
        score = 8
        quality = "good form with minor deviation"
    elif diff <= 30:
        score = 6
        quality = "ok form but needs tighter control"
    else:
        score = 4
        quality = "significant gap from target; adjust technique"

    # Very lightweight Laban-style description by joint
    laban_map = {
        "left_knee": "Stomp (1.0) -> Ground (0.5) -> Recover (1.0)",
        "right_knee": "Stomp (1.0) -> Ground (0.5) -> Recover (1.0)",
        "left_hip": "Shift (1.0) -> Drop (0.5) -> Rise (1.0)",
        "right_hip": "Shift (1.0) -> Drop (0.5) -> Rise (1.0)",
        "left_shoulder": "Lift (1.0) -> Jab (0.5) -> Swing (1.0)",
        "right_shoulder": "Lift (1.0) -> Jab (0.5) -> Swing (1.0)",
        "left_elbow": "Guard (1.0) -> Jab (0.5) -> Reset (1.0)",
        "right_elbow": "Guard (1.0) -> Jab (0.5) -> Reset (1.0)",
    }
    laban = laban_map.get(joint, "Stomp (1.0) -> Jab (0.5) -> Arm Swing (1.0)")

    smooth_text = {
        "low": "very smooth and controlled",
        "medium": "reasonably smooth with some variation",
        "high": "explosive with noticeable variation between frames",
    }.get(str(smoothness).lower(), f"smoothness={smoothness}")

    reps = meta.get("reps")
    reps_line = f"Reps detected: **{reps}**\n" if reps is not None else ""

    return (
        f"Joint: **{joint}**\n"
        f"Target angle: **{target:.1f}°**\n"
        f"Observed (average in clip): **{observed:.1f}°**\n"
        f"{reps_line}"
        f"Score: **{score}/10** — {quality}.\n"
        f"Movement smoothness: {smooth_text}.\n"
        f"Laban: {laban}\n\n"
        f"Krump for life! Remember to warm up the joint and stop if you feel sharp pain."
    )


def forward_to_openclaw(joint: str, target: float, observed: float, smoothness: str) -> None:
    """
    Optionally forward the analysis summary to the OpenClaw gateway so KrumpPhysio
    can decide about Canton logging / Stripe / Anyway traces.

    Controlled by environment variables:
    - OPENCLAW_GATEWAY_TOKEN: bearer token for gateway auth (required)
    - OPENCLAW_GATEWAY_URL: base URL for responses endpoint
      (default: http://127.0.0.1:18789/v1/responses)
    """
    token = os.environ.get("OPENCLAW_GATEWAY_TOKEN")
    if not token:
        return

    url = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789/v1/responses")

    input_text = (
        "System: This message comes from the KrumpPhysio video sidecar bot. "
        "Treat it as if the patient had just provided these measured angles "
        "after a video analysis, and respond in your usual KrumpPhysio style, "
        "including deciding whether to log to Canton and/or create a Stripe link if appropriate.\n\n"
        f"Measured joint data from video:\n"
        f"- joint: {joint}\n"
        f"- target_angle_deg: {target:.1f}\n"
        f"- observed_angle_deg: {observed:.1f}\n"
        f"- smoothness: {smoothness}\n"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": "krumpbot-fit",
    }
    payload = {
        "model": "openclaw",
        "input": input_text,
    }

    try:
        # #region agent log
        log_path = REPO_ROOT / ".cursor" / "debug-b06977.log"
        debug_payload = {
            "sessionId": "b06977",
            "runId": "video-bot-post-fix",
            "hypothesisId": "H_openclaw_forward",
            "location": "video/telegram_bot.py:forward_to_openclaw",
            "message": "Forwarding analysis to OpenClaw responses API",
            "data": {
                "url": url,
                "joint": joint,
                "target": target,
                "observed": observed,
                "smoothness": smoothness,
            },
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(debug_payload) + "\n")
        # #endregion

        with httpx.Client(timeout=5.0) as client:
            client.post(url, headers=headers, json=payload)
    except Exception:
        # Swallow errors so the Telegram reply still succeeds even if gateway is down
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "KrumpPhysio Video Bot ready.\n"
        "Send a short video with a caption like:\n"
        "  /analyze left_knee 90\n"
        "or\n"
        "  left_shoulder 120\n"
        "and I'll analyse the joint angle from the clip."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None:
        return

    if not (message.video or (message.document and message.document.mime_type.startswith("video/"))):
        return

    parsed = parse_caption(message.caption)
    if not parsed:
        await message.reply_text(
            "I need a caption with the joint and target angle, e.g.:\n"
            "`/analyze left_knee 90` or `right_shoulder 120`",
        )
        return

    joint, target = parsed

    # Download video
    tg_file = await context.bot.get_file(
        message.video.file_id if message.video else message.document.file_id
    )
    local_path = VIDEO_DIR / f"{message.chat_id}_{message.message_id}.mp4"

    await tg_file.download_to_drive(custom_path=str(local_path))

    try:
        data = run_analysis(local_path, joint, target)
        reply_text = build_reply_from_analysis(data, joint, target)
        # Also forward a compact summary to the OpenClaw gateway so KrumpPhysio
        # can handle Canton/Stripe/Anyway as usual.
        summary = data.get("summary") or []
        meta = data.get("meta") or {}
        if summary:
            observed = float(summary[0].get("observed", target))
            smoothness = str(meta.get("smoothness", "unknown"))
            forward_to_openclaw(joint, target, observed, smoothness)
    except Exception as exc:  # noqa: BLE001
        await message.reply_text(
            "Sorry, I couldn't analyse that clip.\n"
            f"Details: {exc}\n"
            "Try a shorter, clearer video (3–5 seconds) focusing on a single joint."
        )
        return

    # #region agent log
    try:
        log_path = REPO_ROOT / ".cursor" / "debug-b06977.log"
        payload = {
            "sessionId": "b06977",
            "runId": "video-bot-post-fix",
            "hypothesisId": "H_markdown",
            "location": "video/telegram_bot.py:reply",
            "message": "About to send Telegram reply",
            "data": {
                "joint": joint,
                "target": target,
                "reply_preview": reply_text[:200],
            },
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass
    # #endregion

    await message.reply_text(reply_text)


def main() -> None:
    """Entry point for running the Telegram video bot."""
    token = os.environ.get("KRUMP_VIDEO_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "Set KRUMP_VIDEO_BOT_TOKEN in your environment with your Telegram bot token."
        )

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            handle_video,
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()

