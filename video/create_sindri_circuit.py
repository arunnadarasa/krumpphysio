#!/usr/bin/env python3
"""
One-off script: create the attestation circuit on Sindri and add its ID to .env.

Uses the multiplier2 circuit from Sindri-Labs/sindri-resources (accepts a,b integers).
Run from repo root with SINDRI_API_KEY in .env, or:

  export SINDRI_API_KEY=your_key
  python video/create_sindri_circuit.py

Requires: pip install sindri (already in video/requirements.txt).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(env_path: Path) -> None:
    """Load .env into os.environ (simple KEY=VAL, no quotes)."""
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
    env_path = REPO_ROOT / ".env"
    load_dotenv(env_path)

    api_key = os.environ.get("SINDRI_API_KEY")
    if not api_key:
        print("SINDRI_API_KEY not set. Add it to .env or export it.", file=sys.stderr)
        return 1

    tmp = tempfile.mkdtemp(prefix="sindri-resources-")
    try:
        repo_dir = Path(tmp) / "sindri-resources"
        print("Cloning sindri-resources (multiplier2 circuit)...")
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/Sindri-Labs/sindri-resources.git", str(repo_dir)],
            check=True,
            capture_output=True,
        )
        circuit_path = repo_dir / "circuit_database" / "circom" / "multiplier2"
        if not circuit_path.exists():
            print(f"Circuit path not found: {circuit_path}", file=sys.stderr)
            return 1

        print("Uploading and compiling circuit on Sindri (this may take a minute)...")
        from sindri import Sindri

        sindri = Sindri(api_key, verbose_level=0)
        circuit_id = sindri.create_circuit(str(circuit_path), wait=True)
        print(f"Circuit created: {circuit_id}")

        # Append to .env
        new_line = f"\nSINDRI_ATTESTATION_CIRCUIT_ID={circuit_id}\n"
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(new_line)
        print(f"Appended SINDRI_ATTESTATION_CIRCUIT_ID to {env_path}")

        return 0
    except subprocess.CalledProcessError as e:
        print(f"Git clone failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
