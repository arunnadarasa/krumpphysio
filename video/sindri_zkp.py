"""
Optional ZKP attestation for Telegram → OpenClaw payload (FLock inference input).

When SINDRI_API_KEY is set, we can generate a proof that the payload we send
to OpenClaw (joint, target, observed, smoothness) is consistent with a
committed value. Uses Sindri's Python SDK.

See docs/SINDRI-ZKP-TELEGRAM-FLOCK.md for design and references.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional

# Optional: only used when SINDRI_API_KEY is set
_sindri_client: Optional[Any] = None


def _get_sindri():
    """Lazy init Sindri client from env."""
    global _sindri_client
    if _sindri_client is not None:
        return _sindri_client
    key = os.environ.get("SINDRI_API_KEY")
    if not key:
        return None
    try:
        from sindri import Sindri

        _sindri_client = Sindri(key, verbose_level=0)
        return _sindri_client
    except Exception:
        return None


def attest_payload(
    joint: str, target: float, observed: float, smoothness: str
) -> Optional[dict]:
    """
    Optionally generate a ZK proof attesting the analysis payload.

    Returns None if SINDRI_API_KEY is unset or proof generation fails.
    Otherwise returns a dict with:
      - proof_id: str (Sindri proof UUID)
      - public_output: optional (e.g. commitment / circuit public output)
      - circuit_id: optional (circuit used)

    We use a simple encoding: target and observed as integers (rounded) for
    a PoC circuit. If SINDRI_ATTESTATION_CIRCUIT_ID is set, we use that
    circuit (must accept the proof_input we send). Otherwise we skip
    proof generation unless you've deployed a compatible circuit and set
    the env var.
    """
    sindri = _get_sindri()
    if not sindri:
        return None

    circuit_id = os.environ.get("SINDRI_ATTESTATION_CIRCUIT_ID")
    if not circuit_id:
        # No circuit configured: return a commitment only (no Sindri call).
        # Caller can still send this to OpenClaw for integrity checks.
        commitment = hashlib.sha256(
            f"{joint}|{target}|{observed}|{smoothness}".encode()
        ).hexdigest()
        return {"commitment": commitment, "proof_id": None, "circuit_id": None}

    # Encode payload for a circuit that expects at least two numeric inputs.
    # Standard sindri-resources multiplier2 expects {"a": int, "b": int}.
    # We encode: a = hash of (joint,smoothness) mod 2^31, b = round(target)*1000 + round(observed)
    a_val = int(hashlib.sha256(f"{joint}|{smoothness}".encode()).hexdigest()[:8], 16) % (2**31)
    b_val = int(round(target) * 1000 + round(observed))

    proof_input = json.dumps({"a": a_val, "b": b_val})

    try:
        proof_id = sindri.prove_circuit(circuit_id, proof_input, wait=True)
        if not proof_id:
            return None
        detail = sindri.get_proof(proof_id, include_proof=False, include_public=True)
        public = detail.get("public") if isinstance(detail.get("public"), (list, dict)) else None
        return {
            "proof_id": proof_id,
            "public_output": public,
            "circuit_id": circuit_id,
        }
    except Exception:
        return None
