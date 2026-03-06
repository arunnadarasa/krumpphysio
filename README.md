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
  - **Use the correct Stripe account:** For the Anyway bounty we use a dedicated **“Anyway US sandbox”** Stripe account. Make sure `STRIPE_SECRET_KEY` comes from that sandbox (not a personal Stripe account), and complete the basic account verification Stripe asks for in its dashboard, or payments/links may not appear where you expect.
  - **Create a payment link (no CLI needed):** `node canton/create-stripe-link.js --amount <cents> --currency gbp --description "..."` — requires `STRIPE_SECRET_KEY` in `.env`. The script uses the Stripe Node SDK, sets `quantity: 1`, and attaches metadata (`service_name=krumpbot-fit`, `service_type=physiotherapy`, `tracing_id=KRUMPPHYSIO-...`, `environment=sandbox`) so you can correlate links and payments in the Stripe dashboard.
  - **Test product link (sandbox):** [KrumpPhysio Session — £5/month](https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00) (for hackathon / Anyway bounty submission).
  - **Validated flow:** From OpenClaw Chat/Telegram, KrumpPhysio runs `exec` → Stripe Payment Link is created in the **Anyway US sandbox** with metadata → a £5 test payment succeeds → the agent run and exec call appear as traces in the Anyway sandbox under `krumpbot-fit`.

**Summary:** Anyway = measure and prove; Stripe = get paid. Website/product copy: [docs/website-description.md](docs/website-description.md). See also [docs/STRIPE-INTEGRATION-FIX.md](docs/STRIPE-INTEGRATION-FIX.md) and [docs/STRIPE-INTEGRATION-FIX-PROTOCOL.md](docs/STRIPE-INTEGRATION-FIX-PROTOCOL.md) for failure modes and full protocol.

### Optional: Quantum-inspired exercise optimisation (Guppy + Selene)

Use [Guppy](https://docs.quantinuum.com/guppy/) (quantum programming in Python) and [Selene](https://docs.quantinuum.com/selene/) (Quantinuum’s emulator) to produce a **quantum-inspired exercise focus** (upper / lower / core / full) and intensity for the week. The agent runs the script via **exec** from both **OpenClaw Chat** and **Telegram** when KrumpPhysio is the default agent, and replies with a short coaching message (focus, intensity, tip, “Krump for life!”, health tip). Best practices: [docs/BEST-PRACTICES.md](docs/BEST-PRACTICES.md), [docs/OPENCLAW-TELEGRAM-READINESS.md](docs/OPENCLAW-TELEGRAM-READINESS.md).

```bash
# Guppy requires Python 3.10+. If python3 --version is 3.9, use python3.11 (e.g. brew install python@3.11).
python3.11 -m venv .venv-quantum && source .venv-quantum/bin/activate   # or python3 if already 3.10+
pip install --upgrade pip && pip install -r quantum/requirements.txt

# Run
python quantum/optimise_exercises.py --shots 5
# Output: JSON with focus, intensity, shots (for battle-round schedule)
```

If `pip install` fails with "Could not find guppylang", see [quantum/README.md](quantum/README.md) (Python 3.10+ and pip upgrade). Compatible with the [ClawHub quantum skill](https://clawhub.ai/arunnadarasa/quantum) (Quantinuum hackathon).

### Optional: ElevenLabs (voice + music — Option B)

With **OpenClaw/FLock as the brain**, ElevenLabs is used only for **TTS**, **STT**, and **music** in the Telegram video bot:

- **TTS:** After each video analysis reply, the bot can send the same feedback as a voice message (accessibility / language barriers).
- **STT:** Users can send a voice note (e.g. “left knee 90”); the bot transcribes it and tells them the exact caption to use for their video.
- **Music:** Optionally generate a short instrumental beat after each analysis (set `ELEVENLABS_MUSIC_AFTER_ANALYSIS=1`).

Set `ELEVENLABS_API_KEY` in `.env` (see [.env.example](.env.example)). Install `video/requirements.txt` into `.venv-video` (includes `elevenlabs` and `httpx`). Implementation: [video/elevenlabs_voice.py](video/elevenlabs_voice.py).

**Language coverage:** TTS uses **eleven_v3** by default (70+ languages); override with `ELEVENLABS_TTS_MODEL_ID`. STT uses **scribe_v2** (90+ languages) with auto language detection; the bot passes the user’s Telegram `language_code` when available for better accuracy. Together this covers all languages offered by ElevenLabs.

---

See the project breakdown (Notion) for stages and timeline, and the official SDG 3 specification for context:

- [Notion project breakdown](https://www.notion.so/NOTION_PROJECT_BREAKDOWN-316818b184638041a4a0fc2c40e8db34)
- [SDG 3 – Good Health and Well-being](https://sdgs.un.org/goals/goal3)
