#!/usr/bin/env python3
"""
Quantum-inspired exercise optimisation using Guppy + Selene.

Uses Guppy to define a small hybrid quantum program (2-qubit circuit),
Selene to run it (emulated), and maps the measurement outcome to an
exercise focus and intensity for the week. The agent can call this via
exec and use the result in coaching.

Usage:
  python quantum/optimise_exercises.py [--shots 5] [--seed 42]
  Outputs JSON to stdout: {"focus": "upper|lower|core|full", "intensity": "light|moderate|strong", "shots": [...]}

Requires: pip install -r quantum/requirements.txt
"""

import argparse
import json
import sys
from pathlib import Path

# Map 2-bit outcome to exercise focus (Krump-friendly)
FOCUS_MAP = {
    (0, 0): "upper",
    (0, 1): "lower",
    (1, 0): "core",
    (1, 1): "full",
}

INTENSITY_LEVELS = ["light", "moderate", "strong"]


def main():
    parser = argparse.ArgumentParser(description="Quantum-inspired exercise optimisation (Guppy + Selene)")
    parser.add_argument("--shots", type=int, default=5, help="Number of shots for majority vote")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    try:
        from guppylang import guppy
        from guppylang.std.quantum import qubit, h, measure
        from guppylang.std.builtins import result
    except ImportError as e:
        sys.stderr.write(json.dumps({"error": "Missing guppylang", "detail": str(e)}) + "\n")
        sys.exit(1)

    try:
        from selene_sim import build
    except ImportError as e:
        sys.stderr.write(json.dumps({"error": "Missing selene-sim", "detail": str(e)}) + "\n")
        sys.exit(1)

    # --- Guppy: define the quantum program (2 qubits, H on both, measure) ---
    @guppy
    def exercise_circuit() -> None:
        q0: qubit = qubit()
        q1: qubit = qubit()
        h(q0)
        h(q1)
        m0 = measure(q0)
        m1 = measure(q1)
        result("m0", m0)
        result("m1", m1)

    # --- Compile (Guppy) and build runner (Selene) ---
    try:
        hugr = exercise_circuit.compile()
        runner = build(hugr)
    except Exception as e:
        sys.stderr.write(json.dumps({"error": "Guppy compile or Selene build failed", "detail": str(e)}) + "\n")
        sys.exit(1)

    # --- Run shots (Selene) ---
    try:
        from hugr.qsystem.result import QsysResult, QsysShot
        from selene_sim import Quest
    except ImportError as e:
        sys.stderr.write(json.dumps({"error": "Missing hugr/selene components", "detail": str(e)}) + "\n")
        sys.exit(1)

    simulator = Quest(random_seed=args.seed) if args.seed is not None else Quest()
    try:
        raw = runner.run_shots(simulator, n_qubits=2, n_shots=args.shots)
        shots_result = QsysResult(raw)
    except Exception as e:
        sys.stderr.write(json.dumps({"error": "Selene run failed", "detail": str(e)}) + "\n")
        sys.exit(1)

    # --- Interpret shots: each shot has entries [(name, value), ...] ---
    shots = []
    results_list = getattr(shots_result, "results", shots_result)
    if not isinstance(results_list, (list, tuple)):
        results_list = list(shots_result) if hasattr(shots_result, "__iter__") else []
    for shot in results_list:
        entries = getattr(shot, "entries", None) or []
        d = dict(entries) if entries else {}
        m0 = d.get("m0", 0)
        m1 = d.get("m1", 0)
        m0 = 1 if m0 in (True, 1) else 0
        m1 = 1 if m1 in (True, 1) else 0
        key = (m0, m1)
        focus = FOCUS_MAP.get(key, "full")
        shots.append({"m0": m0, "m1": m1, "focus": focus})

    # Majority vote for focus; intensity from shot count (demo)
    focus_counts = {}
    for s in shots:
        f = s["focus"]
        focus_counts[f] = focus_counts.get(f, 0) + 1
    best_focus = max(focus_counts, key=focus_counts.get)
    intensity = INTENSITY_LEVELS[min(args.shots % 3, 2)]

    out = {
        "focus": best_focus,
        "intensity": intensity,
        "shots": shots,
        "note": "Quantum-inspired schedule from Guppy + Selene. Use focus for this week's battle rounds.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
