# OpenClaw tool: log session to Canton (Telegram / agent-decides)

So that the agent can **decide** when to persist a scoring session to the Canton ledger (e.g. after replying on Telegram), you need to register a tool that runs the CLI wrapper.

### Current limitation (OpenClaw 2026.3.x)

**This OpenClaw version does not support custom tool definitions in `~/.openclaw/openclaw.json`.** Adding a block like `tools.log_krumpphysio_session` causes "Unrecognized key" and prevents the gateway from loading.

**What to do instead:** Use the built-in **exec** tool. The agent (e.g. krumpbot-fit) already has `exec` available. In `agent/IDENTITY.md` we instruct it to run the Canton log script via exec after giving a movement score:  
`node /Users/openclaw/Documents/KrumpPhysio/canton/log-session.js --score <score> --round <round> --angles '<angles_json>' --notes '<your_reply>'`  
No config change is required; ensure the agent’s workspace can run `node` and that the path above is correct for your machine. For manual runs or automation, use the **CLI** (see §1 below). When a future OpenClaw version supports custom tools in config, you can add a dedicated `log_krumpphysio_session` tool and point it at the same script.

## 1. CLI wrapper (already in repo)

From the KrumpPhysio project root:

```bash
node canton/log-session.js --score 9.7 --round 1 --angles '[{"joint":"left_shoulder","target":120,"observed":118}]' --notes "Your full reply text here"
```

- **--score** – numeric score (e.g. 9.7). Optional; defaults to 0.
- **--round** – round label (default "1").
- **--angles** – JSON array of `{joint, target, observed}`. Optional; can be `[]`.
- **--notes** – string (your scoring reply). Optional but recommended.

The script loads `.env` from the KrumpPhysio directory, so ensure `CANTON_ENABLE`, `CANTON_PATIENT_PARTY`, `CANTON_PHYSIO_PARTY`, `CANTON_JWT`, and `CANTON_SESSIONLOG_TEMPLATE_ID` are set there.

## 2. Register the tool in OpenClaw

In your OpenClaw agent config (e.g. under `~/.openclaw` or wherever the KrumpPhysio / krumpbot-fit agent is defined), add a tool the agent can call. The exact schema depends on your OpenClaw version; typically you need:

- **name:** e.g. `log_krumpphysio_session`
- **description:** e.g. "Persist a KrumpPhysio scoring session to the Canton ledger. Call this once after you have given a movement score out of 10, with the score, round, angles (JSON), and your full reply as notes."
- **invocation:** run the Node script with the agent-supplied arguments.

Example (conceptual; adapt to your config format):

```json
{
  "name": "log_krumpphysio_session",
  "description": "Log a KrumpPhysio scoring session to the Canton ledger. Call after giving a movement score: pass score (number), round (string), angles (JSON array of {joint, target, observed}), and notes (your full reply text).",
  "parameters": {
    "score": { "type": "number", "description": "Score out of 10" },
    "round": { "type": "string", "description": "Round identifier, e.g. 1" },
    "angles_json": { "type": "string", "description": "JSON array of angle objects, e.g. [{\"joint\":\"left_shoulder\",\"target\":120,\"observed\":118}]" },
    "notes": { "type": "string", "description": "Your full scoring reply to the user" }
  }
}
```

If your stack uses an **exec**-style tool, wire it to:

- **command:** `node`
- **args:**  
  `["/Users/openclaw/Documents/KrumpPhysio/canton/log-session.js", "--score", "<score>", "--round", "<round>", "--angles", "<angles_json>", "--notes", "<notes>"]`

(Replace `<score>`, `<round>`, `<angles_json>`, `<notes>` with the placeholders your framework uses for tool parameters.)

## 3. Agent instructions (IDENTITY)

The agent’s `agent/IDENTITY.md` in this repo already instructs it to call `log_krumpphysio_session` after giving a score when the tool is available. Ensure the agent’s workspace includes this repo so it sees that instruction and the tool description.

## 4. Flow (Telegram → Canton)

1. User sends a scoring request (e.g. angles + round) on Telegram.
2. Agent replies with score, feedback, Laban notation.
3. Agent calls `log_krumpphysio_session` with that score, round, angles, and the reply as notes.
4. OpenClaw runs `node canton/log-session.js ...`, which calls `ledgerClient.logSessionToCanton` and creates a `SessionLog` on the ledger.
5. You can confirm with `node canton/summary.js` or in Navigator.
