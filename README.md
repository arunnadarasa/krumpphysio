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

### Optional: Anyway & Stripe

- **Anyway** – LLM observability: set `ANYWAY_API_KEY` in `.env` and use the Python wrapper:
  ```bash
  # from repo root, with .venv created as per docs
  source .venv/bin/activate
  python -m telemetry.trace_score '[{"joint":"left_shoulder","target":120,"observed":118}]' 1
  ```
  This initialises `Traceloop.init(app_name=\"krumpphysio\", api_endpoint=\"collector.anyway.sh:4317\", headers={Authorization: Bearer ANYWAY_API_KEY})` and then calls `node score.js ...` so each scoring session is traced in Anyway.
- **Stripe** – Payments: set `STRIPE_SECRET_KEY` (and optionally `STRIPE_WEBHOOK_SECRET`) in `.env` for paid sessions or subscriptions. Never commit `.env`; use [.env.example](.env.example) as a template.

---

See the project breakdown (Notion) for stages and timeline, and the official SDG 3 specification for context:

- [Notion project breakdown](https://www.notion.so/NOTION_PROJECT_BREAKDOWN-316818b184638041a4a0fc2c40e8db34)
- [SDG 3 – Good Health and Well-being](https://sdgs.un.org/goals/goal3)
