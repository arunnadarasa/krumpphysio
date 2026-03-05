# OpenClaw → Telegram: What Actually Runs

## Channel behaviour (observed)

- **OpenClaw Chat and Telegram** — When **KrumpPhysio (krumpbot-fit)** is the **default agent** (first in `agents.list`) and the Telegram channel is bound to krumpbot-fit, **exec runs on both**. The agent runs the quantum script (and Stripe/Canton scripts) when the user asks (e.g. "Give me a quantum-inspired exercise plan") and replies with the **comprehensive coaching message** (focus, intensity, tip, "Krump for life!", health tip).
- **Best practice:** Paste a short **instruction** first (in Chat or at the start of a Telegram thread) that tells the agent to run the exec command and reply with the coaching format — not raw JSON and not long metaphor tables. See [BEST-PRACTICES.md](BEST-PRACTICES.md).

### Make KrumpPhysio the default agent (dashboard Chat)

If the dashboard **Chat** shows "LovaDance (Agent Asura)" and returns only JSON for quantum requests, the Chat is using the **default** agent (often the first in `agents.list`), which is `krump-agent`, not KrumpPhysio.

To have the dashboard Chat use **KrumpPhysio** (and thus the comprehensive quantum reply) by default:

1. Open your OpenClaw config (e.g. `~/.openclaw/openclaw.json`).
2. Under `agents.list`, **put `krumpbot-fit` (KrumpPhysio) first** in the array, before `krump-agent`. For example, reorder so the first entry is:
   ```json
   {
     "id": "krumpbot-fit",
     "name": "KrumpPhysio",
     "workspace": "/Users/openclaw/.openclaw/workspace/krumpfit-agent",
     "agentDir": "/Users/openclaw/.openclaw/agents/krumpbot-fit",
     "model": "flock/qwen3-235b-a22b-thinking-2507"
   }
   ```
3. Save, then restart the OpenClaw gateway. The dashboard Chat should now use KrumpPhysio by default and return the full coaching message for quantum-inspired plan requests.

---

Paste this into OpenClaw chat so the agent uses the **real** commands (no custom tools exist).

---

**Correction:** You do **not** have tools named `create_stripe_payment_link` or `log_krumpphysio_session`. Use **exec** only:

1. **Quantum-inspired plan**  
   Run **exec** with this **exact** command (Python + venv — there is no Node `generate.js` or `quantum-guppy-selene` in this repo):
   ```bash
   /Users/openclaw/Documents/KrumpPhysio/.venv-quantum/bin/python /Users/openclaw/Documents/KrumpPhysio/quantum/optimise_exercises.py --shots 5
   ```
   Parse the JSON and reply with a **short coaching message** (not raw JSON): state focus and intensity, one practical tip for that focus (upper→jabs/arms; lower→stomps/legs; core→buck/stability; full→full-body), then "Krump for life!" and a one-line health tip. See [BEST-PRACTICES.md](BEST-PRACTICES.md).

2. **Payment link**  
   Run **exec** with (no Stripe CLI):
   ```bash
   node /Users/openclaw/Documents/KrumpPhysio/canton/create-stripe-link.js --amount <cents> --currency gbp --description "KrumpPhysio session"
   ```
   Script accepts `--amount` or `--price` (cents). Use the URL from the JSON output.

3. **Canton session log**  
   After giving a movement score, run **exec** once with:
   ```bash
   node /Users/openclaw/Documents/KrumpPhysio/canton/log-session.js --score <score> --round <round> --angles '<json>' --notes '<your_reply>'
   ```

Your instructions are in `agent/IDENTITY.md`. Use **exec** with these exact commands on both Chat and Telegram; there are no other tools for quantum, Stripe, or Canton. **Best practices:** [BEST-PRACTICES.md](BEST-PRACTICES.md).
