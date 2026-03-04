# Stripe Integration Fix Protocol

*Validated on OpenClaw 2026.3.2 with Qwen models*

**Quick setup:** See [STRIPE-PROTOCOL-QUICKSTART.md](STRIPE-PROTOCOL-QUICKSTART.md) for a 5-minute checklist.

## Core Issues Resolved

| Issue | Symptom | Impact |
|-------|---------|--------|
| CLI Syntax Error | `Unknown command "payment-links"` | Complete failure |
| Missing Dependencies | `Cannot find module 'stripe'` | Execution crash |
| Environment Variables | `Neither apiKey nor config.authenticator provided` | Security failure |
| API Parameters | `Missing required param: line_items[0][quantity]` | Silent failure |
| Tool Permissions | `Command not found: create_stripe_payment_link` | Permission denied |
| Runtime Context | `agentId not allowed for sessions_spawn` | Incorrect execution context |

---

## Step-by-Step Implementation Guide

### 1. Switch to Stripe Node.js Library (Critical)

*Replace error-prone CLI with reliable SDK*

```bash
# Install required packages
cd /path/to/your/agent/workspace
npm install stripe dotenv
```

**Payment script** (`canton/create-stripe-link.js`) uses the Stripe SDK, `quantity: 1`, and loads `.env` from repo root. See the file in this repo for the full implementation.

### 2. Secure Environment Configuration

```bash
# Create .env file (gitignored)
echo "STRIPE_SECRET_KEY=sk_test_your_key_here" >> .env

# Verify .env is in .gitignore
grep -q '^\.env$' .gitignore || echo ".env" >> .gitignore
```

Never commit real keys. Use [.env.example](../.env.example) as a template.

### 3. OpenClaw Tool Configuration

**Note for OpenClaw 2026.3.x:** Custom tool definitions in `~/.openclaw/openclaw.json` are not supported (unrecognized keys). Use the **exec** tool instead: the agent runs `node /path/to/KrumpPhysio/canton/create-stripe-link.js --price <cents> --currency <code> --description "..."`. See [agent/IDENTITY.md](../agent/IDENTITY.md) and [STRIPE.md](STRIPE.md).

*If your OpenClaw version supports custom tools*, you could configure:

```json
{
  "tools": {
    "create_stripe_payment_link": {
      "description": "Create Stripe payment links with proper parameters",
      "exec": {
        "command": "node",
        "args": [
          "canton/create-stripe-link.js",
          "--price", "{amount}",
          "--currency", "{currency}",
          "--description", "{description}"
        ],
        "cwd": "/path/to/your/workspace"
      },
      "parameters": {
        "type": "object",
        "properties": {
          "amount": { "type": "number", "description": "Amount in cents" },
          "currency": { "type": "string", "description": "Currency code" },
          "description": { "type": "string", "description": "Payment description" }
        },
        "required": ["amount", "description"]
      }
    }
  }
}
```

### 4. Agent Tool Permissions

*If using custom tools:* Ensure the agent has the tool in its allow list. In 2026.3.x, agents use **exec** with the script path; no tool registration is required.

### 5. ACP Runtime Configuration (when using sessions_spawn)

*Required for proper agent context when spawning subagents*

```bash
# Install ACP runtime plugin (if needed)
npm install -g @openclawd/acpx
```

**Update `openclaw.json` plugins** (if using ACP):

```json
{
  "plugins": {
    "allow": ["acpx"],
    "entries": {
      "acpx": {
        "enabled": true,
        "config": {
          "defaultAgent": "your-agent-id"
        }
      }
    }
  }
}
```

**Restart gateway:**

```bash
openclaw gateway restart
```

### 6. Correct Subagent Spawning

*Use ACP runtime for tool access when spawning*

```bash
openclaw sessions spawn \
  --runtime acp \
  --agent your-agent-id \
  --task "Create Stripe payment link for $10.00" \
  --model flock-qwen-thinking
```

*In code:*

```json
{
  "runtime": "acp",
  "agentId": "your-agent-id",
  "task": "Create payment link...",
  "model": "flock-qwen-thinking"
}
```

---

## Verification Protocol

### 1. Manual Test

```bash
cd /path/to/workspace
node canton/create-stripe-link.js --price 1000 --currency usd --description "Test"
# Expected: {"url":"https://buy.stripe.com/...","id":"plink_..."}
```

### 2. Anyway Observability Check

*Confirm traces appear in dashboard:*

Filter in Anyway: `service.name = "your-agent-id"` and look for exec/tool spans that run the script.

### 3. Production Validation

```bash
curl -sI $(node canton/create-stripe-link.js --price 100 --currency usd --description test | jq -r .url) | grep HTTP
# Should return: HTTP/2 200
```

---

## Common Pitfalls & Fixes

| Error | Solution |
|-------|----------|
| `agentId not allowed` | Use `runtime: "acp"` + install acpx plugin when spawning |
| `Missing quantity` | Script includes `quantity: 1` in payment link creation |
| `Command not found` | In 2026.3.x use **exec** with full path to `create-stripe-link.js` |
| `Neither apiKey provided` | Set `STRIPE_SECRET_KEY` in `.env`; script loads from repo root |
| `Invalid string` | Script uses `price_data` (not `price`) in API calls |
| `Unrecognized key: create_stripe_payment_link` | OpenClaw 2026.3.x: do not add custom tools; use exec |

---

## Pro Tips for Other Agents

1. **Parameter pattern for financial tools**  
   Use `amount` (cents), `currency` (ISO code), `description` in script args.

2. **Anyway integration**  
   Enable in config: `captureToolIO: true`, `serviceName`: your agent id.

3. **Error handling**  
   Script exits with code 1 and JSON error on failure; guard for missing `STRIPE_SECRET_KEY`.

4. **Security**  
   Keep `.env` and `secrets/` in `.gitignore`; never commit API keys.

---

## See also

- [STRIPE-PROTOCOL-QUICKSTART.md](STRIPE-PROTOCOL-QUICKSTART.md) — 5-minute quick setup
- [STRIPE.md](STRIPE.md) — Setup and usage
- [STRIPE-INTEGRATION-FIX.md](STRIPE-INTEGRATION-FIX.md) — Shorter fix guide
- [agent/IDENTITY.md](../agent/IDENTITY.md) — Exec command for payment links
