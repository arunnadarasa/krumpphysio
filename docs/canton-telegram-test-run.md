# Canton + Telegram integration — test run

End-to-end check: Canton ledger running → agent scores on Telegram → session logged to Canton → verify in summary/Navigator.

## Prerequisites

- **Daml SDK** on PATH (`daml`, `damlc`). Java 17+ for Sandbox.
- **Node** (for `log-session.js`, `summary.js`, `jwt-dev.js`). From repo root: `npm install` (for `dotenv`).
- **`.env`** in KrumpPhysio root with Canton vars (see [canton/CANTON.md](../canton/CANTON.md)):
  - `CANTON_ENABLE=true`
  - `CANTON_JSON_API_BASE_URL=http://localhost:7575`
  - `CANTON_PATIENT_PARTY`, `CANTON_PHYSIO_PARTY` (full party IDs, e.g. `sandbox::1220...`)
  - `CANTON_JWT` (from `node canton/jwt-dev.js`)
  - Optional: `CANTON_SESSIONLOG_TEMPLATE_ID` if you rebuilt the DAR
- **OpenClaw** gateway running with Telegram + krumpbot-fit agent (workspace that includes this repo or has access to the log-session path).

---

## Step 1 — Start Canton (Daml Sandbox + JSON API)

In a terminal:

```bash
cd /Users/openclaw/canton/krumpphysio-daml
daml start
```

Leave this running. You should see Sandbox, Navigator, and JSON API (e.g. JSON API on port 7575). Allocate parties if you haven’t yet:

```bash
daml ledger allocate-party --host localhost --port 6865 KrumpPhysioPatient
daml ledger allocate-party --host localhost --port 6865 KrumpPhysioClinic
```

Put the returned party identifiers in `.env` as `CANTON_PATIENT_PARTY` and `CANTON_PHYSIO_PARTY`. Generate JWT and set `CANTON_JWT`:

```bash
cd /Users/openclaw/Documents/KrumpPhysio
node canton/jwt-dev.js
# paste output into .env as CANTON_JWT=...
```

---

## Step 2 — Smoke test: CLI log + summary (no Telegram)

From KrumpPhysio root, with Canton and `.env` in place:

```bash
node canton/log-session.js --score 9.5 --round 1 --angles '[{"joint":"left_shoulder","target":120,"observed":118}]' --notes "CLI smoke test"
```

You should see no error (or a success message if we add one). Then:

```bash
node canton/summary.js
```

You should see at least one `SessionLog` (the one you just created). If either command fails, fix Canton/JWT/parties/template ID before testing Telegram.

---

## Step 3 — Start OpenClaw gateway

In another terminal, start OpenClaw so the Telegram binding and krumpbot-fit agent are active. Example (adjust if you use a different command):

```bash
openclaw start
# or: npx openclaw start
```

Ensure the krumpbot-fit agent’s workspace can run `node` and that the path in IDENTITY is correct:  
`node /Users/openclaw/Documents/KrumpPhysio/canton/log-session.js ...`

---

## Step 4 — Trigger a score on Telegram

From Telegram (group or DM bound to krumpbot-fit), send a message that asks for a movement score, e.g.:

- *“Score my left shoulder: target 120°, observed 118°, round 1. Give me score out of 10, feedback, and Laban notation.”*

The agent should:

1. Reply with score, feedback, and Laban notation.
2. Use the **exec** tool to run the Canton log script with that score, round, angles, and reply text (per [agent/IDENTITY.md](../agent/IDENTITY.md)).

---

## Step 5 — Verify on Canton

- **Summary script:** From KrumpPhysio root run `node canton/summary.js` and confirm a new SessionLog for the session you just triggered.
- **Navigator:** Open the Navigator URL from `daml start` (e.g. http://localhost:3000), find the `SessionLog` template and confirm the latest contract.

---

## Troubleshooting

| Symptom | Check |
|--------|--------|
| `CANTON_PATIENT_PARTY and CANTON_PHYSIO_PARTY must be set` | `.env` in KrumpPhysio root, vars set; `dotenv` loads from project root when you run `node canton/log-session.js` from repo root. |
| 401 from JSON API | JWT missing or wrong. Regenerate with `node canton/jwt-dev.js`; ensure `CANTON_LEDGER_ID` and party IDs in `.env` match the sandbox. |
| 400 template ID / payload | Use full template ID `packageId:Module:Entity`. Rebuild DAR → new package ID → update `CANTON_SESSIONLOG_TEMPLATE_ID`. |
| Agent doesn’t run log script | Agent must have **exec** and IDENTITY instructing it to run the log command after scoring. Confirm workspace and path to `log-session.js`. |
| Exec fails (path not found) | Use absolute path in IDENTITY; ensure OpenClaw process can run `node` and that the path exists on the machine. |

---

## Quick reference

- **Canton setup:** [canton/CANTON.md](../canton/CANTON.md)  
- **Agent logging (exec):** [canton/OPENCLAW-TOOL.md](../canton/OPENCLAW-TOOL.md)  
- **Agent identity:** [agent/IDENTITY.md](../agent/IDENTITY.md)
