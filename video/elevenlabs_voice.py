"""
ElevenLabs integration for KrumpPhysio (Option B: TTS, STT, Music only).

- TTS: convert reply text to speech for voice messages (accessibility / language).
- STT: transcribe voice messages to text so users can speak instead of type.
- Music: generate short bespoke beats for exercise rounds (engagement).

Language support (all languages offered by ElevenLabs):
- TTS: default model eleven_v3 supports 70+ languages. Override with ELEVENLABS_TTS_MODEL_ID.
- STT: scribe_v2 supports 90+ languages with auto language detection; optional language_code
  improves accuracy when known (e.g. from Telegram user.language_code).

Requires ELEVENLABS_API_KEY in the environment. All functions return None or
empty bytes on missing key or API errors so the bot keeps working without ElevenLabs.
Uses the ElevenLabs Python SDK for TTS/STT (lazy import, so missing SDK just disables sound)
and direct HTTP (httpx) for music.
"""

from __future__ import annotations

import os
from io import BytesIO
from typing import Optional, Any

_BASE = "https://api.elevenlabs.io"

_client: Optional[Any] = None


def _api_key() -> Optional[str]:
    return os.environ.get("ELEVENLABS_API_KEY") or None


def _log_debug(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    """
    Append a single NDJSON debug line to the shared debug log.
    Safe no-op on any error.
    """
    try:
        import json
        import time
        from pathlib import Path

        log_path = Path(__file__).resolve().parent.parent / ".cursor" / "debug-b06977.log"
        payload = {
            "sessionId": "b06977",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        # Never let logging break core flow
        pass


def _get_client():
    """
    Lazily construct an ElevenLabs client.
    Returns None if API key or SDK are not available.
    """
    global _client
    if _client is not None:
        return _client

    api_key = _api_key()
    if not api_key:
        _log_debug("EL1", "video/elevenlabs_voice.py:_get_client", "No API key", {})
        return None

    try:
        from elevenlabs.client import ElevenLabs  # type: ignore[import-not-found]
    except Exception as e:  # noqa: BLE001
        _log_debug(
            "EL1",
            "video/elevenlabs_voice.py:_get_client",
            "SDK import failed",
            {"error_type": type(e).__name__, "error_message": str(e)[:200]},
        )
        return None

    try:
        _client = ElevenLabs(api_key=api_key)
        _log_debug(
            "EL1",
            "video/elevenlabs_voice.py:_get_client",
            "Client constructed",
            {},
        )
        return _client
    except Exception as e:  # noqa: BLE001
        _log_debug(
            "EL1",
            "video/elevenlabs_voice.py:_get_client",
            "Client construction failed",
            {"error_type": type(e).__name__, "error_message": str(e)[:200]},
        )
        return None


def text_to_speech(text: str, voice_id: Optional[str] = None) -> Optional[bytes]:
    """
    Convert text to speech. Returns MP3 bytes or None.
    Uses eleven_v3 by default (70+ languages). Truncates very long text for Telegram.
    Override model via ELEVENLABS_TTS_MODEL_ID (e.g. eleven_turbo_v2_5 for lower latency).
    """
    if not text or not text.strip():
        return None

    client = _get_client()
    if not client:
        _log_debug(
            "EL2",
            "video/elevenlabs_voice.py:text_to_speech",
            "No client (skipping TTS)",
            {},
        )
        return None

    max_chars = 1000
    if len(text) > max_chars:
        text = text[: max_chars - 3].rsplit(maxsplit=1)[0] + "..."

    voice = voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or "JBFqnCBsd6RMkjVDRZzb"
    model_id = os.environ.get("ELEVENLABS_TTS_MODEL_ID") or "eleven_v3"

    try:
        audio = client.text_to_speech.convert(  # type: ignore[attr-defined]
            text=text,
            voice_id=voice,
            model_id=model_id,
            output_format="mp3_44100_128",
        )
        _log_debug(
            "EL2",
            "video/elevenlabs_voice.py:text_to_speech",
            "TTS call succeeded",
            {"model_id": model_id},
        )
    except Exception as e:  # noqa: BLE001
        _log_debug(
            "EL2",
            "video/elevenlabs_voice.py:text_to_speech",
            "TTS call failed",
            {"error_type": type(e).__name__, "error_message": str(e)[:200]},
        )
        return None

    # SDK may return bytes, a stream-like object, or an iterator of chunks
    if hasattr(audio, "read"):
        try:
            data = audio.read()
            _log_debug(
                "EL2",
                "video/elevenlabs_voice.py:text_to_speech",
                "Stream read",
                {"content_len": len(data) if data else 0},
            )
            return data
        except Exception as e:  # noqa: BLE001
            _log_debug(
                "EL2",
                "video/elevenlabs_voice.py:text_to_speech",
                "Stream read failed",
                {"error_type": type(e).__name__, "error_message": str(e)[:200]},
            )
            return None
    # Handle iterable / generator of byte chunks
    try:
        from collections.abc import Iterable

        if isinstance(audio, Iterable) and not isinstance(audio, (bytes, bytearray, str)):
            chunks = []
            for chunk in audio:
                if isinstance(chunk, (bytes, bytearray)):
                    chunks.append(bytes(chunk))
            data = b"".join(chunks)
            _log_debug(
                "EL2",
                "video/elevenlabs_voice.py:text_to_speech",
                "Iterable result",
                {"content_len": len(data)},
            )
            return data or None
    except Exception as e:  # noqa: BLE001
        _log_debug(
            "EL2",
            "video/elevenlabs_voice.py:text_to_speech",
            "Iterable handling failed",
            {"error_type": type(e).__name__, "error_message": str(e)[:200]},
        )
    if isinstance(audio, (bytes, bytearray)):
        data = bytes(audio)
        _log_debug(
            "EL2",
            "video/elevenlabs_voice.py:text_to_speech",
            "Bytes result",
            {"content_len": len(data)},
        )
        return data
    return None


def speech_to_text(
    audio_bytes: bytes,
    language_code: Optional[str] = None,
) -> Optional[str]:
    """
    Transcribe audio to text. Accepts raw bytes (ogg/mp3/wav).
    Uses scribe_v2 (90+ languages). Pass language_code (ISO-639-1, e.g. 'es', 'ar')
    when known to improve accuracy; otherwise language is auto-detected.
    Returns None on failure or missing key.
    """
    if not audio_bytes:
        return None

    client = _get_client()
    if not client:
        return None

    model_id = os.environ.get("ELEVENLABS_STT_MODEL_ID") or "scribe_v2"

    kwargs: dict[str, Any] = {"model_id": model_id}
    if language_code and language_code.strip():
        kwargs["language_code"] = language_code.strip()[:10]

    try:
        result = client.speech_to_text.convert(  # type: ignore[attr-defined]
            file=BytesIO(audio_bytes),
            **kwargs,
        )
    except Exception:
        return None

    # Result typically has a .text attribute; fall back to dict form if needed
    text = getattr(result, "text", None)
    if isinstance(text, str) and text.strip():
        return text
    if isinstance(result, dict):
        txt = result.get("text")
        if isinstance(txt, str) and txt.strip():
            return txt
    return None


def generate_music(
    prompt: str,
    duration_sec: int = 30,
    instrumental: bool = True,
) -> Optional[bytes]:
    """
    Generate a short music clip (e.g. for Krump round). Returns MP3 bytes or None.
    Uses ElevenLabs Music API (paid). duration_sec clamped to 3–90 for short rounds.
    """
    api_key = _api_key()
    if not api_key or not prompt:
        return None
    duration_ms = max(3000, min(90000, duration_sec * 1000))
    try:
        import httpx

        with httpx.Client(timeout=90.0) as client:
            r = client.post(
                f"{_BASE}/v1/music/stream",
                headers={
                    "xi-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "prompt": prompt[:500],
                    "music_length_ms": duration_ms,
                    "model_id": "music_v1",
                    "force_instrumental": instrumental,
                },
            )
        _log_debug(
            "ELM",
            "video/elevenlabs_voice.py:generate_music",
            "Music API response",
            {"status_code": r.status_code, "content_len": len(r.content or b"")},
        )
        if r.status_code != 200:
            return None
        return r.content or None
    except Exception as e:  # noqa: BLE001
        _log_debug(
            "ELM",
            "video/elevenlabs_voice.py:generate_music",
            "Music API exception",
            {"error_type": type(e).__name__, "error_message": str(e)[:200]},
        )
        return None
