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

import asyncio
import base64
import json
import os
import subprocess
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

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

# Load .env for FLOCK_API_KEY (Kimi commands)
_env_file = REPO_ROOT / ".env"
if _env_file.exists():
    with open(_env_file, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                _k, _v = _k.strip(), _v.strip().strip("'\"")
                if _k:
                    os.environ.setdefault(_k, _v)

# FLock/Kimi (platform.flock.io) for /kimi_image, /kimi_video, /kimi_gen_image
FLOCK_API_KEY = os.environ.get("FLOCK_API_KEY")
FLOCK_KIMI_MODEL = os.environ.get("FLOCK_KIMI_MODEL", "kimi-k2.5")
FLOCK_CHAT_URL = "https://api.flock.io/v1/chat/completions"

# Replicate for real LLM-generated image and video
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
REPLICATE_IMAGE_MODEL = os.environ.get("REPLICATE_IMAGE_MODEL", "black-forest-labs/flux-schnell")
REPLICATE_VIDEO_MODEL = os.environ.get("REPLICATE_VIDEO_MODEL", "minimax/video-01")

# KrumpGotchi assets for /exercise_demo and Kimi exercises
KRUMPGOTCHI_AVATAR = REPO_ROOT / "docs" / "krumpgotchi-assets" / "krumpgotchi-avatar.png"
KRUMPGOTCHI_VIDEO = (
    REPO_ROOT / "docs" / "krumpgotchi-assets" / "exercises" / "sample.mp4"
    if (REPO_ROOT / "docs" / "krumpgotchi-assets" / "exercises" / "sample.mp4").exists()
    else REPO_ROOT / "video" / "samples" / "test_video.mp4"
)

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


def _call_kimi_image(image_path: Path) -> Tuple[str, str]:
    """Call FLock Kimi with an image; returns (content, reasoning)."""
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image in one or two sentences. It is the KrumpGotchi mascot for a rehab app. What do you see?"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }
    ]
    payload = {"model": FLOCK_KIMI_MODEL, "messages": messages, "max_tokens": 1024}
    headers = {"Content-Type": "application/json", "Accept": "application/json", "x-litellm-api-key": FLOCK_API_KEY}
    resp = httpx.post(FLOCK_CHAT_URL, headers=headers, json=payload, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = (msg.get("content") or "").strip()
    reasoning = (msg.get("reasoning_content") or "").strip()
    return content, reasoning


def _call_kimi_text_only(user_prompt: str) -> str:
    """Call FLock Kimi with text only; returns content (no image/video)."""
    messages = [{"role": "user", "content": user_prompt}]
    payload = {"model": FLOCK_KIMI_MODEL, "messages": messages, "max_tokens": 512}
    headers = {"Content-Type": "application/json", "Accept": "application/json", "x-litellm-api-key": FLOCK_API_KEY}
    resp = httpx.post(FLOCK_CHAT_URL, headers=headers, json=payload, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    return (msg.get("content") or "").strip()


def _generate_image_replicate(prompt: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Generate an image via Replicate (e.g. FLUX). Returns (image_bytes, error_message)."""
    if not REPLICATE_API_TOKEN:
        return None, "REPLICATE_API_TOKEN not set (add to .env and restart the bot)."
    # Replicate client reads from os.environ; ensure it's set
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
    try:
        import replicate
        output = replicate.run(
            REPLICATE_IMAGE_MODEL,
            input={"prompt": prompt[:1000]},
        )
        if not output:
            return None, "Replicate returned no output."
        first = list(output)[0] if hasattr(output, "__iter__") and not isinstance(output, str) else output
        if isinstance(first, str) and first.startswith("http"):
            r = httpx.get(first, timeout=30.0)
            r.raise_for_status()
            return r.content, None
        if hasattr(first, "read"):
            return first.read(), None
        return None, "Unexpected Replicate output format."
    except Exception as e:
        err = str(e).strip() or repr(e)
        if len(err) > 400:
            err = err[:397] + "..."
        return None, err


def _generate_video_replicate(prompt: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Generate a short video via Replicate (e.g. minimax/video-01). Returns (video_bytes, error_message)."""
    if not REPLICATE_API_TOKEN:
        return None, "REPLICATE_API_TOKEN not set (add to .env and restart the bot)."
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
    try:
        import replicate
        # Video gen can take 1–2 min; replicate.run() blocks until done
        output = replicate.run(
            REPLICATE_VIDEO_MODEL,
            input={"prompt": prompt[:500], "prompt_optimizer": True},
        )
        if not output:
            return None, "Replicate returned no output."
        # minimax/video-01 output schema is type=string, format=uri (single video URL)
        # Replicate Python client can return: URI string, FileOutput, iterable of bytes (stream), or single bytes
        first = output
        if isinstance(output, dict):
            first = (
                output.get("video")
                or output.get("output")
                or output.get("url")
                or (list(output.values())[0] if output else None)
            )
        elif hasattr(output, "__iter__") and not isinstance(output, (str, bytes)):
            out_list = list(output)
            if not out_list:
                return None, "Replicate returned empty output."
            first = out_list[0]
            # If iterable of bytes (streaming), join all chunks into one video file
            if isinstance(first, bytes) and all(isinstance(x, bytes) for x in out_list):
                return b"".join(out_list), None
            if isinstance(first, dict):
                first = first.get("video") or first.get("output") or first.get("url") or list(first.values())[0]
        if not first:
            return None, "Replicate returned no output."
        # Single bytes (full video)
        if isinstance(first, bytes) and len(first) > 0:
            return first, None
        # FileOutput: has .url or .read()
        if hasattr(first, "url") and first.url:
            r = httpx.get(first.url, timeout=60.0)
            r.raise_for_status()
            return r.content, None
        if hasattr(first, "read"):
            return first.read(), None
        # URI string (output schema: type string, format uri)
        if isinstance(first, str) and first.startswith("http"):
            r = httpx.get(first, timeout=60.0)
            r.raise_for_status()
            return r.content, None
        return None, f"Unexpected Replicate video output format (type={type(first).__name__})."
    except Exception as e:
        err = str(e).strip() or repr(e)
        if len(err) > 400:
            err = err[:397] + "..."
        return None, err


def _call_kimi_video(video_path: Path) -> Tuple[str, str]:
    """Call FLock Kimi with a video; returns (content, reasoning)."""
    with open(video_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode("ascii")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Watch this short video. In 1–2 sentences, what is the person doing?"},
                {"type": "video_url", "video_url": {"url": f"data:video/mp4;base64,{b64}"}},
            ],
        }
    ]
    payload = {"model": FLOCK_KIMI_MODEL, "messages": messages, "max_tokens": 1024}
    headers = {"Content-Type": "application/json", "Accept": "application/json", "x-litellm-api-key": FLOCK_API_KEY}
    resp = httpx.post(FLOCK_CHAT_URL, headers=headers, json=payload, timeout=120.0)
    resp.raise_for_status()
    data = resp.json()
    choice = data.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = (msg.get("content") or "").strip()
    reasoning = (msg.get("reasoning_content") or "").strip()
    return content, reasoning


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

    If SINDRI_API_KEY is set, we optionally attach a ZK attestation (proof_id or
    commitment) so FLock/OpenClaw can verify the payload. See docs/SINDRI-ZKP-TELEGRAM-FLOCK.md.

    Controlled by environment variables:
    - OPENCLAW_GATEWAY_TOKEN: bearer token for gateway auth (required)
    - OPENCLAW_GATEWAY_URL: base URL for responses endpoint
      (default: http://127.0.0.1:18789/v1/responses)
    - SINDRI_API_KEY: if set, attest payload and include proof/commitment in forward
    - SINDRI_ATTESTATION_CIRCUIT_ID: optional circuit ID for full proof (e.g. multiplier2)
    """
    token = os.environ.get("OPENCLAW_GATEWAY_TOKEN")
    if not token:
        return

    url = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789/v1/responses")

    # Optional ZKP attestation (commitment or proof_id) for verifiable Telegram → FLock input
    zkp_note = ""
    try:
        import importlib.util
        _spec = importlib.util.spec_from_file_location(
            "sindri_zkp", REPO_ROOT / "video" / "sindri_zkp.py"
        )
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        att = _mod.attest_payload(joint, target, observed, smoothness)
        if att:
            if att.get("proof_id"):
                zkp_note = (
                    f"\n[ZKP attestation: proof_id={att['proof_id']}, "
                    f"circuit_id={att.get('circuit_id', '')} — verifiable via Sindri API]"
                )
            elif att.get("commitment"):
                zkp_note = f"\n[Payload commitment (SHA-256): {att['commitment']}]"
    except Exception:
        pass

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
        f"{zkp_note}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-openclaw-agent-id": "krumpbot-fit",
        # Privacy layer for OpenClaw/FLock: mark message as minimal-PII, from video bot (no identifiers in body)
        "X-KrumpPhysio-Source": "video-bot",
        "X-KrumpPhysio-Privacy": "attested-no-pii",
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
    """Welcome message: list of commands and prompt for patient name, interest, limbs."""
    msg = (
        "👋 **Welcome to KrumpPhysio**\n\n"
        "I’m here to help with movement and rehab. You can send a short video with a caption like "
        "`/analyze left_knee 90` and I’ll analyse the joint angle from the clip.\n\n"
        "**Commands**\n"
        "• /help — show this again\n"
        "• /privacy — how we use your data\n"
        "• /link — link Telegram to KrumpGotchi website\n"
        "• /exercise_demo — see KrumpGotchi image + sample video\n"
        "• /kimi_image — KrumpGotchi image + Kimi’s description\n"
        "• /kimi_video — sample video + Kimi’s description\n"
        "• /kimi_gen_image — AI-generated exercise image (Kimi + Replicate)\n"
        "• /kimi_gen_video — AI-generated exercise video (Kimi + Replicate)\n\n"
        "**About you (optional)**\n"
        "When you’re ready, reply with:\n"
        "• Your name (or what to call you)\n"
        "• What you’re interested in (e.g. rehab, physio, knee recovery)\n"
        "• Limbs you want to work on (e.g. left knee, right shoulder)\n"
        "Joints I can analyse: left/right shoulder, elbow, hip, knee.\n\n"
    )
    if os.environ.get("ELEVENLABS_API_KEY"):
        msg += "_You can also send a voice note with the joint and angle (e.g. “left knee 90”)._\n\n"
    msg += "_Videos are only used for movement analysis on our server. /privacy for more._"
    if os.environ.get("LINK_WEBSITE_URL"):
        msg += "\n_Link to KrumpGotchi: /link_"
    await update.message.reply_text(msg)


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Short privacy notice for patients; reassures and supports health-authority confidence."""
    msg = (
        "**Privacy — KrumpPhysio Video Bot**\n\n"
        "• Your video is used only to analyse the joint angle you asked for. Analysis runs on our server; we do not send your video to other companies.\n"
        "• We only keep the numbers (joint, target, observed angle, smoothness) so your coach can give you feedback. The operator can delete your video right after analysis.\n"
        "• When optional privacy tech (zero-knowledge proofs) is enabled, we can prove the analysis was done correctly without sharing your video or identity.\n"
        "• For full details and operator checklist, see the project docs (PRIVACY.md)."
    )
    await update.message.reply_text(msg)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def exercise_demo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send KrumpGotchi avatar (image) and a sample exercise video so the user can
    test image + video in Telegram. See docs/TEST-RUN-EXERCISES.md.
    """
    message = update.message
    if not message or not message.chat:
        return
    chat_id = message.chat_id

    if not KRUMPGOTCHI_AVATAR.exists():
        await message.reply_text(
            f"KrumpGotchi avatar not found at {KRUMPGOTCHI_AVATAR}. Add the image and try /exercise_demo again."
        )
        return
    if not KRUMPGOTCHI_VIDEO.exists():
        await message.reply_text(
            f"Exercise video not found. Add docs/krumpgotchi-assets/exercises/sample.mp4 or ensure video/samples/test_video.mp4 exists."
        )
        return

    await message.reply_photo(
        photo=str(KRUMPGOTCHI_AVATAR),
        caption="KrumpGotchi — avatar (image exercise)",
    )
    await message.reply_video(
        video=str(KRUMPGOTCHI_VIDEO),
        caption="KrumpGotchi — video exercise demo",
    )


async def kimi_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send the KrumpGotchi avatar image and Kimi (FLock) LLM-generated description.
    Requires FLOCK_API_KEY from platform.flock.io in .env or environment.
    """
    message = update.message
    if not message or not message.chat:
        return
    if not FLOCK_API_KEY:
        await message.reply_text(
            "Kimi image exercise needs FLOCK_API_KEY (from platform.flock.io). "
            "Add it to .env or the environment and restart the bot."
        )
        return
    if not KRUMPGOTCHI_AVATAR.exists():
        await message.reply_text(f"Avatar not found: {KRUMPGOTCHI_AVATAR}")
        return
    status = await message.reply_text("One moment — asking Kimi about the image…")
    try:
        content, reasoning = _call_kimi_image(KRUMPGOTCHI_AVATAR)
    except Exception as e:
        await status.edit_text(f"Kimi API error: {e!s}")
        return
    caption = f"Kimi (image exercise):\n\n{content}" if content else "Kimi (image exercise): (no reply)"
    if len(caption) > 1020:
        caption = caption[:1017] + "..."
    await status.delete()
    await message.reply_photo(photo=str(KRUMPGOTCHI_AVATAR), caption=caption)
    if reasoning and len(reasoning) < 3000:
        await message.reply_text(f"<i>Reasoning:</i>\n{reasoning[:3000]}", parse_mode="HTML")


async def kimi_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send the exercise video and Kimi (FLock) LLM-generated description.
    Requires FLOCK_API_KEY from platform.flock.io. Video may not be seen by Kimi (proxy limit).
    """
    message = update.message
    if not message or not message.chat:
        return
    if not FLOCK_API_KEY:
        await message.reply_text(
            "Kimi video exercise needs FLOCK_API_KEY (from platform.flock.io). "
            "Add it to .env or the environment and restart the bot."
        )
        return
    if not KRUMPGOTCHI_VIDEO.exists():
        await message.reply_text("Exercise video not found. Add sample.mp4 or test_video.mp4.")
        return
    status = await message.reply_text("One moment — asking Kimi about the video…")
    try:
        content, reasoning = _call_kimi_video(KRUMPGOTCHI_VIDEO)
    except Exception as e:
        await status.edit_text(f"Kimi API error: {e!s}")
        return
    caption = f"Kimi (video exercise):\n\n{content}" if content else "Kimi (video exercise): (no reply)"
    if len(caption) > 1020:
        caption = caption[:1017] + "..."
    await status.delete()
    await message.reply_video(video=str(KRUMPGOTCHI_VIDEO), caption=caption)
    if reasoning and len(reasoning) < 3000:
        await message.reply_text(f"<i>Reasoning:</i>\n{reasoning[:3000]}", parse_mode="HTML")


async def kimi_gen_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Real LLM-generated image: Kimi suggests an image prompt, then Replicate (FLUX) generates
    the image. Send that image in Telegram. Requires FLOCK_API_KEY and REPLICATE_API_TOKEN.
    """
    message = update.message
    if not message or not message.chat:
        return
    if not FLOCK_API_KEY:
        await message.reply_text("Set FLOCK_API_KEY (platform.flock.io) for Kimi to suggest the image idea.")
        return
    if not REPLICATE_API_TOKEN:
        await message.reply_text(
            "Real image generation needs REPLICATE_API_TOKEN (replicate.com/account/api-tokens). "
            "Then Kimi will suggest an image idea and Replicate will draw it."
        )
        return
    status = await message.reply_text("Asking Kimi for an image idea…")
    try:
        prompt_idea = _call_kimi_text_only(
            "In one short sentence (under 15 words), suggest an image generation prompt for a "
            "KrumpGotchi rehab exercise: a cute mascot character (crab-like, friendly) doing a "
            "simple physio movement. Output only the prompt, no quotes or explanation."
        )
    except Exception as e:
        await status.edit_text(f"Kimi error: {e!s}")
        return
    if not prompt_idea or len(prompt_idea) > 500:
        prompt_idea = "A friendly crab mascot in a snapback and jacket doing a gentle knee bend, cartoon style"
    await status.edit_text("Generating image…")
    image_bytes, gen_error = _generate_image_replicate(prompt_idea)
    if not image_bytes:
        msg = "Image generation failed."
        if gen_error:
            msg += f" {gen_error}"
        await status.edit_text(msg)
        return
    await status.delete()
    caption = f"Kimi suggested: “{prompt_idea[:200]}”"
    if len(caption) > 1020:
        caption = caption[:1017] + "..."
    bio = BytesIO(image_bytes)
    bio.name = "exercise.png"
    bio.seek(0)
    await message.reply_photo(photo=bio, caption=caption)


async def kimi_gen_video_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Real LLM-generated video: Kimi suggests a video prompt, then Replicate (e.g. minimax/video-01)
    generates a short video. Can take 1–2 minutes. Requires FLOCK_API_KEY and REPLICATE_API_TOKEN.
    """
    message = update.message
    if not message or not message.chat:
        return
    if not FLOCK_API_KEY:
        await message.reply_text("Set FLOCK_API_KEY (platform.flock.io) for Kimi to suggest the video idea.")
        return
    if not REPLICATE_API_TOKEN:
        await message.reply_text(
            "Real video generation needs REPLICATE_API_TOKEN (replicate.com/account/api-tokens)."
        )
        return
    status = await message.reply_text("Asking Kimi for a video idea…")
    try:
        prompt_idea = _call_kimi_text_only(
            "In one short sentence (under 15 words), suggest a video generation prompt for a "
            "KrumpGotchi rehab exercise: a cute mascot (crab-like) doing a simple physio movement. "
            "Output only the prompt, no quotes or explanation."
        )
    except Exception as e:
        await status.edit_text(f"Kimi error: {e!s}")
        return
    if not prompt_idea or len(prompt_idea) > 500:
        prompt_idea = "A friendly crab mascot in a snapback doing a gentle knee bend, cartoon style"
    await status.edit_text("Generating video (1–2 min)…")
    try:
        video_bytes, gen_error = await asyncio.to_thread(
            _generate_video_replicate, prompt_idea
        )
    except Exception as e:
        await status.edit_text(f"Video generation error: {e!s}")
        return
    if not video_bytes:
        msg = "Video generation failed."
        if gen_error:
            msg += f" {gen_error}"
        await status.edit_text(msg)
        return
    await status.delete()
    caption = f"Kimi suggested: \"{prompt_idea[:200]}\""
    if len(caption) > 1020:
        caption = caption[:1017] + "..."
    bio = BytesIO(video_bytes)
    bio.name = "exercise.mp4"
    bio.seek(0)
    await message.reply_video(video=bio, caption=caption)


async def link_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate a one-time code so the user can link this Telegram account to the
    KrumpGotchi website. Set LINK_WEBSITE_URL in env (e.g. https://your-app.lovable.app).
    """
    message = update.message
    if not message or not message.from_user:
        return
    user = message.from_user
    telegram_id = user.id
    chat_id = message.chat_id if message.chat else telegram_id
    username = user.username

    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        "telegram_link_codes", REPO_ROOT / "video" / "telegram_link_codes.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    code = _mod.create_code(telegram_id, chat_id, username)

    url = os.environ.get("LINK_WEBSITE_URL", "https://your-krumpgotchi-site.com")
    msg = (
        "**Link your Telegram to KrumpGotchi**\n\n"
        f"Your one-time code: `{code}`\n\n"
        f"Enter this code at the website within 5 minutes:\n{url}\n\n"
        "After linking, your KrumpGotchi and points will sync with this account."
    )
    await message.reply_text(msg)


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
        summary = data.get("summary") or []
        meta = data.get("meta") or {}
        observed = float(summary[0].get("observed", target)) if summary else target
        smoothness = str(meta.get("smoothness", "unknown")) if meta else "unknown"
    except Exception as exc:  # noqa: BLE001
        await message.reply_text(
            "Sorry, I couldn't analyse that clip.\n"
            f"Details: {exc}\n"
            "Try a shorter, clearer video (3–5 seconds) focusing on a single joint."
        )
        return

    # Reply to the user immediately so we don't hit Telegram timeout. Sindri ZKP and
    # OpenClaw forward can take 30–60+ s; run them after replying (in a thread).
    await message.reply_text(reply_text)

    # Forward to OpenClaw (and optionally generate Sindri proof) in background so
    # the bot stays responsive and the user already has their analysis.
    if summary:
        import asyncio
        asyncio.create_task(asyncio.to_thread(forward_to_openclaw, joint, target, observed, smoothness))

    # Privacy: delete video after analysis if operator enables it (reassures patients & health authorities)
    if os.environ.get("KRUMP_VIDEO_DELETE_AFTER_ANALYSIS", "").strip().lower() in ("1", "true", "yes"):
        try:
            if local_path.exists():
                local_path.unlink()
        except OSError:
            pass

    # Optional: ElevenLabs TTS — send same reply as voice (Option B: voice for accessibility)
    # #region agent log
    _log_path = REPO_ROOT / ".cursor" / "debug-b06977.log"
    try:
        _has_key = bool(os.environ.get("ELEVENLABS_API_KEY"))
        with open(_log_path, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({"sessionId": "b06977", "hypothesisId": "H1", "location": "video/telegram_bot.py:tts_block", "message": "TTS block entered", "data": {"ELEVENLABS_API_KEY_set": _has_key}, "timestamp": int(time.time() * 1000)}) + "\n")
    except Exception:
        pass
    # #endregion
    try:
        from elevenlabs_voice import text_to_speech
        tts_text = reply_text.replace("**", "").strip()
        audio_bytes = text_to_speech(tts_text) if tts_text else None
        # #region agent log
        try:
            _res = "none" if audio_bytes is None else f"bytes_{len(audio_bytes)}"
            with open(_log_path, "a", encoding="utf-8") as _f:
                _f.write(json.dumps({"sessionId": "b06977", "hypothesisId": "H2", "location": "video/telegram_bot.py:after_tts", "message": "text_to_speech result", "data": {"result": _res}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        if audio_bytes:
            # #region agent log
            try:
                with open(_log_path, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({"sessionId": "b06977", "hypothesisId": "H3", "location": "video/telegram_bot.py:before_reply_voice", "message": "sending voice", "data": {"len_bytes": len(audio_bytes)}, "timestamp": int(time.time() * 1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            await message.reply_voice(voice=BytesIO(audio_bytes), filename="reply.ogg")
    except Exception as _e:
        # #region agent log
        try:
            with open(_log_path, "a", encoding="utf-8") as _f:
                _f.write(json.dumps({"sessionId": "b06977", "hypothesisId": "H3", "location": "video/telegram_bot.py:tts_exception", "message": "reply_voice or TTS failed", "data": {"error_type": type(_e).__name__, "error_message": str(_e)[:200]}, "timestamp": int(time.time() * 1000)}) + "\n")
        except Exception:
            pass
        # #endregion
        pass

    # Optional: ElevenLabs Music — short beat after analysis (engagement)
    music_flag = os.environ.get("ELEVENLABS_MUSIC_AFTER_ANALYSIS", "").lower()
    # #region agent log
    try:
        with open(_log_path, "a", encoding="utf-8") as _f:
            _f.write(
                json.dumps(
                    {
                        "sessionId": "b06977",
                        "hypothesisId": "M1",
                        "location": "video/telegram_bot.py:music_flag",
                        "message": "Music flag check",
                        "data": {"ELEVENLABS_MUSIC_AFTER_ANALYSIS": music_flag},
                        "timestamp": int(time.time() * 1000),
                    }
                )
                + "\n"
            )
    except Exception:
        pass
    # #endregion
    if music_flag in ("1", "true", "yes"):
        try:
            from elevenlabs_voice import generate_music
            prompt = "30 second instrumental beat, moderate tempo, for dance workout, no vocals"
            music_bytes = generate_music(prompt, duration_sec=30, instrumental=True)
            # #region agent log
            try:
                status = "none" if music_bytes is None else f"bytes_{len(music_bytes)}"
                with open(_log_path, "a", encoding="utf-8") as _f:
                    _f.write(
                        json.dumps(
                            {
                                "sessionId": "b06977",
                                "hypothesisId": "M2",
                                "location": "video/telegram_bot.py:music_result",
                                "message": "generate_music result",
                                "data": {"result": status},
                                "timestamp": int(time.time() * 1000),
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion
            if music_bytes:
                await message.reply_audio(
                    audio=BytesIO(music_bytes),
                    filename="krump_beat.mp3",
                    title="Krump round beat",
                )
        except Exception as _e:
            # #region agent log
            try:
                with open(_log_path, "a", encoding="utf-8") as _f:
                    _f.write(
                        json.dumps(
                            {
                                "sessionId": "b06977",
                                "hypothesisId": "M3",
                                "location": "video/telegram_bot.py:music_exception",
                                "message": "Music generation failed",
                                "data": {
                                    "error_type": type(_e).__name__,
                                    "error_message": str(_e)[:200],
                                },
                                "timestamp": int(time.time() * 1000),
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Transcribe voice with ElevenLabs STT; if it looks like joint + target, guide user to send video."""
    message = update.message
    if not message or not message.voice:
        return

    try:
        from elevenlabs_voice import speech_to_text
    except Exception:
        await message.reply_text("Voice input is not configured. Send a video with a text caption instead, e.g. /analyze left_knee 90")
        return

    tg_file = await context.bot.get_file(message.voice.file_id)
    buf = BytesIO()
    await tg_file.download_to_memory(buf)
    audio_bytes = buf.getvalue()
    if not audio_bytes:
        await message.reply_text("I couldn't read that voice message. Try again or send a text caption with your video.")
        return

    lang = message.from_user.language_code if message.from_user else None
    text = speech_to_text(audio_bytes, language_code=lang)
    if not text or not text.strip():
        await message.reply_text("I couldn't transcribe that. Send a short video with a caption like: /analyze left_knee 90")
        return

    parsed = parse_caption(text) or parse_caption("/analyze " + text.strip())
    if parsed:
        joint, target = parsed
        await message.reply_text(
            f"Got it — {joint} at {target:.0f}°. Send a short video of the movement with caption:\n"
            f"/analyze {joint} {target:.0f}"
        )
        return

    await message.reply_text(
        "I heard you. For movement analysis, send a short video with a caption like:\n"
        "/analyze left_knee 90\n"
        "or say which joint and target angle (e.g. \"left knee 90\") and I'll tell you the exact caption to use."
    )


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
    application.add_handler(CommandHandler("privacy", privacy_command))
    application.add_handler(CommandHandler("link", link_command))
    application.add_handler(CommandHandler("exercise_demo", exercise_demo_command))
    application.add_handler(CommandHandler("kimi_image", kimi_image_command))
    application.add_handler(CommandHandler("kimi_video", kimi_video_command))
    application.add_handler(CommandHandler("kimi_gen_image", kimi_gen_image_command))
    application.add_handler(CommandHandler("kimi_gen_video", kimi_gen_video_command))
    application.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            handle_video,
        )
    )
    application.add_handler(
        MessageHandler(filters.VOICE, handle_voice),
    )

    application.run_polling()


if __name__ == "__main__":
    main()

