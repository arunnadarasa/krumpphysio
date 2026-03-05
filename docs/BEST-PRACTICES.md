# KrumpPhysio — Best practices

Short, proven practices for running the agent (OpenClaw Chat + Telegram) with quantum, Stripe, and Canton.

---

## 1. Make KrumpPhysio the default agent

**Why:** Dashboard Chat and Telegram use the default/first agent. If another agent (e.g. Asura) is first, you get that agent’s behaviour (e.g. raw JSON or long metaphor plans instead of the script-based coaching reply).

**Do:** In `~/.openclaw/openclaw.json`, put **krumpbot-fit (KrumpPhysio)** first in `agents.list`. Restart the OpenClaw gateway after editing.

See [OPENCLAW-TELEGRAM-READINESS.md](OPENCLAW-TELEGRAM-READINESS.md) for the exact JSON snippet.

---

## 2. Paste an instruction first (quantum / exec)

**Why:** Locking in “run exec with this command and reply with a short coaching message” before the first quantum request makes the agent consistently run the script and format the reply (focus + intensity + tip + “Krump for life!” + health tip).

**Do:** In OpenClaw Chat (or at the start of a Telegram conversation), paste a short instruction that states:
- When the user asks for a quantum-inspired plan, run **exec** with the exact venv Python + script path and `--shots 5`.
- Reply with a **short coaching message** (not raw JSON, not long NHS/metaphor tables): state focus and intensity, one practical tip for that focus, then “Krump for life!” and a one-line health tip.
- Do not refuse or invent “NHS lockout” / “metric ban.”

Ask the agent to confirm. Then send: “Give me a quantum-inspired exercise plan for this week.”

---

## 3. Comprehensive reply format (quantum)

**Do not** reply with only `{"focus": "...", "intensity": "..."}`. **Do** reply with:

1. **Battle-round line** — e.g. “This week’s battle rounds: **lower** focus, **strong** intensity — quantum-inspired.”
2. **One practical tip** for that focus: upper → jabs/arm swings; lower → stomps/leg drive; core → buck/stability; full → full-body flow.
3. **Sign-off** — “Krump for life!” + one-line health tip (e.g. “Keep knees slightly bent on impact to protect joints.”).

This is documented in `agent/IDENTITY.md` and the ClawHub skill.

---

## 4. Exec only (no custom tools)

OpenClaw 2026.3.x does not support custom tool definitions in config. Use the **exec** tool only for:

- **Quantum:** `.venv-quantum/bin/python .../quantum/optimise_exercises.py --shots 5`
- **Stripe:** `node .../canton/create-stripe-link.js --amount <cents> --currency gbp --description "..."`
- **Canton log:** `node .../canton/log-session.js --score <score> --round <round> --angles '<json>' --notes '<reply>'`

Paths must be absolute and valid on the machine where the gateway runs. See [OPENCLAW-TELEGRAM-READINESS.md](OPENCLAW-TELEGRAM-READINESS.md).

---

## 5. Chat and Telegram both get exec when default is KrumpPhysio

With **KrumpPhysio first** in `agents.list` and the Telegram binding to krumpbot-fit, **exec runs on both**:

- **OpenClaw Chat** — Agent runs the quantum (and Stripe/Canton) scripts when you ask.
- **Telegram** — Same agent and exec behaviour; patients can request “Give me a quantum-inspired exercise plan” and get the script-backed coaching reply.

If exec ever stops working on one channel, confirm the default agent is still KrumpPhysio and that the binding for that channel is krumpbot-fit; restart the gateway after config changes.

---

## Quick links

| Topic | Doc |
|-------|-----|
| Default agent + paste instruction | [OPENCLAW-TELEGRAM-READINESS.md](OPENCLAW-TELEGRAM-READINESS.md) |
| Exec commands (quantum, Stripe, Canton) | [OPENCLAW-TELEGRAM-READINESS.md](OPENCLAW-TELEGRAM-READINESS.md), [agent/IDENTITY.md](../agent/IDENTITY.md) |
| Stripe setup | [STRIPE.md](STRIPE.md), [STRIPE-PROTOCOL-QUICKSTART.md](STRIPE-PROTOCOL-QUICKSTART.md) |
| Quantum install | [quantum/README.md](../quantum/README.md) |
