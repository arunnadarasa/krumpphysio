# Quantum-inspired exercise optimisation (Guppy + Selene)

KrumpPhysio can use **Guppy** (quantum programming in Python) and **Selene** (Quantinuum’s emulator) to produce a **quantum-inspired exercise focus** for the week: a small 2-qubit circuit is run on Selene, and the measurement outcomes are mapped to focus (upper / lower / core / full) and intensity.

## What this does

- **Guppy** — Defines a 2-qubit circuit (H on both, measure). Compiled to HUGR.
- **Selene** — Runs the program (e.g. Quest simulator) for N shots.
- **Output** — JSON with `focus`, `intensity`, and raw `shots` so the agent can say e.g. “This week’s battle rounds: **upper** focus, **moderate** intensity (quantum-inspired schedule).”

## Install

**Requires Python 3.10 or newer.** Guppy and Selene do not support Python 3.9 or below.

From the repo root:

```bash
# Guppy requires Python 3.10+. macOS often ships 3.9 — use python3.11 explicitly:
#   brew install python@3.11   # if not installed
python3.11 -m venv .venv-quantum
source .venv-quantum/bin/activate   # Windows: .venv-quantum\Scripts\activate

pip install --upgrade pip
pip install -r quantum/requirements.txt
```

**If you see** `Could not find a version that satisfies the requirement guppylang`:

- Your venv was created with Python 3.9 or older. **Recreate the venv with Python 3.10+**, e.g. `python3.11 -m venv .venv-quantum` (after `brew install python@3.11` or [python.org](https://www.python.org/downloads/)). Then activate and run the `pip install` lines again.

## Run

```bash
python quantum/optimise_exercises.py
# optional:
python quantum/optimise_exercises.py --shots 5 --seed 42
```

Output (stdout) is JSON, e.g.:

```json
{
  "focus": "upper",
  "intensity": "moderate",
  "shots": [{"m0": 0, "m1": 0, "focus": "upper"}, ...],
  "note": "Quantum-inspired schedule from Guppy + Selene. Use focus for this week's battle rounds."
}
```

## OpenClaw agent (exec)

When the user asks for a “quantum optimised” or “quantum-inspired” exercise plan, the agent can run:

```bash
python /path/to/KrumpPhysio/quantum/optimise_exercises.py --shots 5
```

Use the **exec** tool; read the JSON from stdout and use `focus` and `intensity` in your reply (e.g. “This week: **upper** focus, **moderate** intensity — battle rounds on jabs and arm swings.”).

## ClawHub quantum skill

For the Quantinuum hackathon or when the agent has the [ClawHub quantum skill](https://clawhub.ai/arunnadarasa/quantum), load that skill so the agent knows when to call this script and how to interpret Guppy/Selene in answers.

## References

- [Guppy](https://docs.quantinuum.com/guppy/) — Python-embedded quantum language
- [Selene](https://docs.quantinuum.com/selene/) — Emulator for hybrid programs
- [Guppy GitHub](https://github.com/Quantinuum/guppylang)
- [Selene GitHub](https://github.com/Quantinuum/selene)
