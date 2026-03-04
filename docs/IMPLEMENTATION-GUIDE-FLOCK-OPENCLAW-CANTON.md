# Full Implementation Guide: FLock, OpenClaw & Canton Network (KrumpPhysio)

Step-by-step guide for the UK AI Agent Hackathon EP4 x OpenClaw: how FLock, OpenClaw, and the Canton Network were integrated for the KrumpPhysio AI physiotherapy coach.

---

## Table of contents

1. [Prerequisites](#1-prerequisites)
2. [FLock: model provider](#2-flock-model-provider)
3. [OpenClaw: agent framework & Telegram](#3-openclaw-agent-framework--telegram)
4. [Canton Network: Daml ledger for session logs](#4-canton-network-daml-ledger-for-session-logs)
5. [Integration: Telegram → agent → Canton](#5-integration-telegram--agent--canton)
6. [Verification & troubleshooting](#6-verification--troubleshooting)
7. [References](#7-references)

---

## 1. Prerequisites

- **Node.js** (v18+): for `score.js`, `canton/log-session.js`, `canton/summary.js`, `canton/jwt-dev.js`.
- **npm**: run `npm install` in the repo root (installs `dotenv`).
- **Daml SDK**: [Install Daml](https://docs.daml.com/getting-started/installation.html) and ensure `daml` and `damlc` are on your PATH. Canton Sandbox needs **Java 17+**; set `JAVA_HOME` if required.
- **OpenClaw**: install globally (e.g. `npm install -g openclaw` or per docs).
- **FLock API key**: from [FLock](https://flock.io) or the hackathon.
- **Telegram Bot Token**: create a bot via [@BotFather](https://t.me/BotFather), then copy the token.

---

## 2. FLock: model provider

FLock is used as the sole LLM provider for the agent (hackathon requirement: no OpenAI/Anthropic in the judging path).

### 2.1 Install the FLock plugin for OpenClaw

```bash
# From anywhere; OpenClaw will install the plugin into its config
openclaw plugins install @openclawd/flock
```

Or add/enable the plugin in OpenClaw config (e.g. `~/.openclaw/openclaw.json` under `plugins.entries.flock` and `plugins.allow`).

### 2.2 Authenticate with FLock

```bash
openclaw models auth login --provider flock
```

When prompted, paste your FLock API key. This stores the credential for OpenClaw.

### 2.3 Configure FLock models in OpenClaw

In `~/.openclaw/openclaw.json`, under `models.providers`, add or ensure a `flock` entry with your API key and model list, for example:

```json
"flock": {
  "baseUrl": "https://api.flock.io/v1",
  "apiKey": "YOUR_FLOCK_API_KEY",
  "api": "openai-completions",
  "models": [
    { "id": "qwen3-235b-a22b-thinking-2507", "name": "Qwen 3 235B Thinking", "reasoning": true, "input": ["text"], "contextWindow": 131072, "maxTokens": 8192 },
    { "id": "qwen3-30b-a3b-instruct-2507", "name": "Qwen 3 30B Instruct", "input": ["text"], "contextWindow": 131072, "maxTokens": 8192 },
    { "id": "deepseek-v3.2", "name": "DeepSeek V3.2", "input": ["text"], "contextWindow": 131072, "maxTokens": 2000 }
  ]
}
```

### 2.4 Assign FLock to the agent

In the same file, under `agents.list`, set your KrumpPhysio agent's `model` to a FLock model ID, e.g.:

```json
{
  "id": "krumpbot-fit",
  "name": "KrumpPhysio",
  "workspace": "/path/to/your/krumpfit-agent-workspace",
  "agentDir": "/path/to/your/openclaw/agents/krumpbot-fit",
  "model": "flock/qwen3-235b-a22b-thinking-2507"
}
```

The agent will then use FLock for all completions.

---

## 3. OpenClaw: agent framework & Telegram

OpenClaw runs the agent, binds it to channels (e.g. Telegram), and provides tools (e.g. `exec`).

### 3.1 Install and configure OpenClaw

- Install OpenClaw (see [OpenClaw docs](https://docs.openclaw.ai)).
- Run the config wizard if needed: `openclaw doctor` or `openclaw wizard`.

### 3.2 Create the agent and workspace

- **Agent directory**: e.g. `~/.openclaw/agents/krumpbot-fit` (or your path). Put identity and instructions here; OpenClaw can also use the repo's `agent/IDENTITY.md` if the workspace points at the repo.
- **Workspace**: e.g. `~/.openclaw/workspace/krumpfit-agent`. This is the agent's working directory; ensure it has access to the KrumpPhysio repo (or copy the repo into the workspace) so that the path to `canton/log-session.js` is valid when the agent runs `exec`.

### 3.3 Agent identity (IDENTITY.md)

In the repo's `agent/IDENTITY.md` (or the agent dir used by OpenClaw), define:

- **Name, creature, vibe**: e.g. KrumpPhysio, AI fitness coach, encouraging and precise.
- **Platform**: OpenClaw + FLock.
- **Coaching guidelines**: Krump vocabulary, Laban notation, score out of 10, feedback.
- **Canton logging**: instruct the agent to use the **exec** tool (not a custom tool) to run the log script after giving a movement score (see §5).

Example Canton section:

```markdown
## Canton logging (after scoring)
- Do not call a tool named `log_krumpphysio_session` — it is not available. Use the **exec** tool only.
- After you give a movement score out of 10, persist the session by calling **exec** exactly once with:
  node /full/path/to/KrumpPhysio/canton/log-session.js --score <score> --round <round> --angles '<angles_json>' --notes '<your_reply>'
```

Replace `/full/path/to/KrumpPhysio` with the actual path on the machine where OpenClaw runs.

### 3.4 Telegram channel

In `~/.openclaw/openclaw.json`:

1. **Channel config** – under `channels.telegram`:
   - `enabled: true`
   - `botToken`: your Telegram bot token from BotFather.
   - Configure `groups` and `dmPolicy` as needed.

2. **Bindings** – under `bindings`, add a binding that routes Telegram messages to your agent, e.g.:

```json
{
  "agentId": "krumpbot-fit",
  "match": {
    "channel": "telegram",
    "peer": { "kind": "group", "id": "YOUR_GROUP_ID" }
  }
},
{
  "agentId": "krumpbot-fit",
  "match": {
    "channel": "telegram",
    "peer": { "kind": "direct", "id": "YOUR_USER_ID" }
  }
}
```

3. **Plugins** – ensure `telegram` is in `plugins.allow` and `plugins.entries.telegram.enabled: true`.

### 3.5 Start the gateway

```bash
openclaw gateway install   # if not already installed
openclaw gateway          # or: launchctl bootstrap ... per OpenClaw docs
```

Once the gateway is running, Telegram messages that match your bindings will be handled by the KrumpPhysio agent using FLock.

---

## 4. Canton Network: Daml ledger for session logs

Session scores are persisted as `SessionLog` contracts on a Daml ledger (Canton Sandbox in development).

### 4.1 Daml project (separate repo or folder)

The Daml project (e.g. `krumpphysio-daml`) contains:

- `daml.yaml` with `sdk-version` (e.g. `2.10.3`) and dependencies.
- A Daml module defining the `SessionLog` template (e.g. `KrumpPhysio.Rehab.SessionLog`) with fields such as `patient`, `physio`, `round`, `score`, `angles`, `notes`.

Build the DAR:

```bash
cd /path/to/krumpphysio-daml
daml build
```

### 4.2 Start the Sandbox and JSON API

From the Daml project directory:

```bash
daml start
```

This starts:

- Daml Sandbox (e.g. port 6865).
- HTTP JSON API (e.g. port 7575).
- Navigator (e.g. port 3000).

Note the **ledger ID** (often `sandbox`) in the console.

### 4.3 Allocate parties

With `daml start` running, in another terminal:

```bash
cd /path/to/krumpphysio-daml
daml ledger allocate-party --host localhost --port 6865 KrumpPhysioPatient
daml ledger allocate-party --host localhost --port 6865 KrumpPhysioClinic
```

Record the full **party identifiers** (e.g. `sandbox::1220...`) for the next step.

### 4.4 KrumpPhysio `.env` (Canton)

In the **KrumpPhysio repo root**, create or edit `.env`:

```bash
# Canton
CANTON_ENABLE=true
CANTON_JSON_API_BASE_URL=http://localhost:7575
CANTON_LEDGER_ID=sandbox
CANTON_PATIENT_PARTY=sandbox::1220...   # full identifier from allocate-party
CANTON_PHYSIO_PARTY=sandbox::1220...    # full identifier from allocate-party
CANTON_JWT=<paste token from step 4.5>
# Optional after first run; set if you rebuild the DAR:
# CANTON_SESSIONLOG_TEMPLATE_ID=<packageId>:KrumpPhysio.Rehab:SessionLog
```

### 4.5 Generate a development JWT

The JSON API requires a Bearer JWT with `ledgerId` and `actAs` (party) claims. From the KrumpPhysio repo:

```bash
cd /path/to/KrumpPhysio
node canton/jwt-dev.js
```

Ensure `CANTON_LEDGER_ID` and `CANTON_PHYSIO_PARTY` are set in `.env` (or exported) before running. Paste the printed token into `.env` as `CANTON_JWT`.

### 4.6 Template ID format

The JSON API expects the template ID as `<packageId>:<module>:<entity>` (two colons). After `daml build`, get the package ID from Navigator or the build output, then set:

```bash
CANTON_SESSIONLOG_TEMPLATE_ID=<packageId>:KrumpPhysio.Rehab:SessionLog
```

If not set, the code uses a default package ID that must match your built DAR.

### 4.7 Node scripts (KrumpPhysio repo)

- **Log a session (CLI):**  
  `node canton/log-session.js --score <score> --round <round> --angles '<json>' --notes "<text>"`  
  Single-hyphen options (`-score`, `-round`, etc.) are also supported. The script loads `.env` from the repo root and calls the Canton JSON API `/v1/create`.

- **Query metrics:**  
  `node canton/summary.js`  
  Prints total sessions and average score from the ledger.

- **JWT generation:**  
  `node canton/jwt-dev.js`  
  Outputs a dev JWT for `CANTON_JWT`.

---

## 5. Integration: Telegram → agent → Canton

End-to-end flow:

1. User sends a scoring request on Telegram (e.g. "Score my right shoulder: target 90°, observed 88°, round 1. Give me score out of 10, feedback, and Laban notation.").
2. OpenClaw routes the message to the KrumpPhysio agent (FLock).
3. The agent replies with score, feedback, and Laban notation.
4. Per `agent/IDENTITY.md`, the agent uses the **exec** tool to run:  
   `node /path/to/KrumpPhysio/canton/log-session.js --score <score> --round <round> --angles '<angles_json>' --notes '<reply>'`  
   so the session is written to Canton.
5. You can verify with `node canton/summary.js` or via Daml Navigator.

**Important:** OpenClaw 2026.3.x does not support defining a custom tool (e.g. `log_krumpphysio_session`) in `openclaw.json`; the agent must use **exec** with the above command. The path must be absolute and valid on the machine where the gateway runs.

---

## 6. Verification & troubleshooting

### 6.1 Canton only (no Telegram)

```bash
# Terminal 1: start ledger
cd /path/to/krumpphysio-daml && daml start

# Terminal 2: log and summarize
cd /path/to/KrumpPhysio
node canton/log-session.js --score 8 --round 1 --angles '[]' --notes "Smoke test"
node canton/summary.js
```

You should see total sessions and average score. If you get 401, regenerate the JWT and update `CANTON_JWT`. If you get 400, check template ID and payload types (e.g. score as number, angles as string in Daml).

### 6.2 Telegram + Canton

1. Start Canton (`daml start`).
2. Start OpenClaw gateway.
3. In Telegram, send a new scoring request (e.g. different joint or round).
4. Run `node canton/summary.js` and confirm a new SessionLog.

If the agent does not run the log script, confirm IDENTITY instructs it to use **exec** with the correct absolute path and that the agent's workspace has access to that path and `node`.

### 6.3 Common issues

| Symptom | Action |
|--------|--------|
| `CANTON_PATIENT_PARTY and CANTON_PHYSIO_PARTY must be set` | Ensure `.env` is in the KrumpPhysio repo root and is loaded (script run from repo root or path resolved from `__dirname`). |
| 401 from JSON API | Regenerate JWT with `node canton/jwt-dev.js`; set `CANTON_LEDGER_ID` and `CANTON_PHYSIO_PARTY` correctly. |
| 400 on create | Use full template ID `packageId:Module:Entity`; ensure payload types match the Daml template (e.g. Decimal for score). |
| Agent doesn't log | Use **exec** with absolute path to `log-session.js`; do not rely on a custom tool in config. |

---

## 7. References

- **FLock:** [FLock API docs](https://docs.flock.io/llms-full.txt), [OpenClaw FLock plugin](https://github.com/FLock-io/openclaw-plugin-flock).
- **OpenClaw:** [OpenClaw docs](https://docs.openclaw.ai), [Exec tool](https://docs.openclaw.ai/tools/exec).
- **Canton / Daml:** [Digital Asset platform docs](https://docs.digitalasset.com/overview/3.4/index.html), [Daml documentation](https://docs.daml.com).
- **KrumpPhysio:** [README](../README.md), [canton/CANTON.md](../canton/CANTON.md), [canton/OPENCLAW-TOOL.md](../canton/OPENCLAW-TOOL.md), [docs/canton-telegram-test-run.md](canton-telegram-test-run.md).
- **Hackathon:** [UK AI Agent Hackathon EP4 x OpenClaw](https://github.com/arunnadarasa/krumpphysio), [FLock track bounty](https://dorahacks.io/hackathon/bounty/1332).
