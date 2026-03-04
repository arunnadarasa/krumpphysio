# KrumpPhysio

AI krump-inspired physiotherapy coach for the **UK AI Agent Hackathon EP4 x OpenClaw**.

- **Goal:** Support **SDG 3 – Good Health and Well-being** with a focus on **Target 3.4 (reduce premature mortality from non-communicable diseases)** by helping people stick to rehab and cardio routines through gamified Krump movement.
- **Concept:** Turn daily physiotherapy and cardio exercises into Krump-style movement challenges. The agent scores form, range of motion and consistency, then frames feedback as a “battle round” to keep motivation high.
- **Stack (high level):** OpenClaw agents using **FLock API Platform** (e.g. `qwen3-235b-a22b-thinking-2507` for brain + `qwen3-30b-a3b-instruct-coding` for code), optional vision / pose-estimation sidecar, KrumpKlaw-style scoring for battles.

### Canton / on-ledger session logs

Session scores can be written to a local Daml ledger (Canton) for auditability and metrics.

1. **Start the ledger** (from the Daml project):
   ```bash
   cd /path/to/krumpphysio-daml   # or your daml project
   daml start
   ```
2. **Configure KrumpPhysio** – create `.env` in this repo with `CANTON_ENABLE=true`, party IDs, JWT, and template ID. See [canton/CANTON.md](canton/CANTON.md) for full setup (parties, JWT, template ID format).
3. **Run a scoring round** (creates a SessionLog contract when Canton is enabled):
   ```bash
   node score.js '[{"joint":"left_shoulder","target":120,"observed":118}]' 1
   ```
4. **View on-ledger metrics**:
   ```bash
   node canton/summary.js
   ```
   Or open **Navigator** at http://localhost:7500 and check **Contracts** as the physio or patient party.

### ClawHub skill for other agents

A [ClawHub skill](skills/krumpphysio/SKILL.md) is included so other OpenClaw agents can learn the KrumpPhysio coach pattern (identity, scoring, Laban notation, optional Canton logging). See [skills/krumpphysio/PUBLISH.md](skills/krumpphysio/PUBLISH.md) for how to publish to ClawHub.

### Optional: Anyway & Stripe (observability + fiat payments)

Together these support **OpenClaw getting paid in fiat when offering physiotherapy to patients**:

- **Anyway** – Observability (traces, token usage, tool IO). Does *not* process payments; it lets you measure and prove what the agent did and what it cost. Set `ANYWAY_API_KEY` in `.env` and use the Python wrapper or the OpenClaw plugin `@anyway-sh/anyway-openclaw`. See [skills/krumpphysio/SKILL.md](skills/krumpphysio/SKILL.md) § Observability.
  ```bash
  source .venv/bin/activate
  python -m telemetry.trace_score '[{"joint":"left_shoulder","target":120,"observed":118}]' 1
  ```
- **Stripe** – Fiat payments: subscriptions, per-session fees, clinic billing. Set `STRIPE_SECRET_KEY` (and optionally `STRIPE_WEBHOOK_SECRET`) in `.env`. Never commit `.env`; use [.env.example](.env.example) as a template.
  - **Create a payment link (no CLI needed):** `node canton/create-stripe-link.js --amount <cents> --currency gbp --description "..."` — requires `STRIPE_SECRET_KEY` in `.env`. See [docs/STRIPE.md](docs/STRIPE.md).
  - **Test product link (sandbox):** [KrumpPhysio Session — £5/month](https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00) (for hackathon / Anyway bounty submission).

**Summary:** Anyway = measure and prove; Stripe = get paid. Website/product copy: [docs/website-description.md](docs/website-description.md).

### Optional: Quantum-inspired exercise optimisation (Guppy + Selene)

Use [Guppy](https://docs.quantinuum.com/guppy/) (quantum programming in Python) and [Selene](https://docs.quantinuum.com/selene/) (Quantinuum’s emulator) to produce a **quantum-inspired exercise focus** (upper / lower / core / full) and intensity for the week. The agent can run the script via **exec** and use the result in coaching.

```bash
# Requires Python 3.10+ (check: python3 --version). Upgrade pip first.
python3 -m venv .venv-quantum && source .venv-quantum/bin/activate
pip install --upgrade pip
pip install -r quantum/requirements.txt

# Run
python quantum/optimise_exercises.py --shots 5
# Output: JSON with focus, intensity, shots (for battle-round schedule)
```

If `pip install` fails with "Could not find guppylang", see [quantum/README.md](quantum/README.md) (Python 3.10+ and pip upgrade). Compatible with the [ClawHub quantum skill](https://clawhub.ai/arunnadarasa/quantum) (Quantinuum hackathon).

---

See the project breakdown (Notion) for stages and timeline, and the official SDG 3 specification for context:

- [Notion project breakdown](https://www.notion.so/NOTION_PROJECT_BREAKDOWN-316818b184638041a4a0fc2c40e8db34)
- [SDG 3 – Good Health and Well-being](https://sdgs.un.org/goals/goal3)
