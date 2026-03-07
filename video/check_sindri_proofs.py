#!/usr/bin/env python3
"""Check if Sindri ZKP ran: list recent proofs for the attestation circuit."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip().strip('"\'')
                if key:
                    os.environ[key] = val


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("SINDRI_API_KEY")
    circuit_id = os.environ.get("SINDRI_ATTESTATION_CIRCUIT_ID")
    if not api_key:
        print("SINDRI_API_KEY not set in .env", file=sys.stderr)
        return 1
    if not circuit_id:
        print("SINDRI_ATTESTATION_CIRCUIT_ID not set (only commitment was used, no proof).", file=sys.stderr)
        return 0

    try:
        from sindri import Sindri
    except ImportError:
        print("Run with: .venv-video/bin/python video/check_sindri_proofs.py", file=sys.stderr)
        return 1

    sindri = Sindri(api_key, verbose_level=0)
    proofs = sindri.get_all_circuit_proofs(circuit_id)
    if not proofs:
        print("No proofs found for this circuit. ZKP may not have run yet, or proof failed.")
        return 0
    # Sort by date_created descending
    proofs = sorted(proofs, key=lambda p: p.get("date_created", ""), reverse=True)
    print(f"Found {len(proofs)} proof(s) for circuit {circuit_id[:8]}...")
    for i, p in enumerate(proofs[:5]):
        pid = p.get("proof_id", "?")
        status = p.get("status", "?")
        created = p.get("date_created", "?")
        print(f"  {i+1}. proof_id={pid[:8]}... status={status} date_created={created}")
    if proofs:
        print("\nZKP is working: at least one proof was generated for your circuit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
