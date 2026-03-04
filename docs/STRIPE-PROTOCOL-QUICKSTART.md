# Stripe Integration Fix Protocol — Quick setup (5 min)

*Verified for OpenClaw agents 2026.3.2+*

## Critical Fixes Summary

| Issue | Fix | Why Critical |
|-------|-----|--------------|
| CLI errors | **Stripe Node.js SDK** | CLI syntax varies by version |
| Missing `quantity` | `quantity: 1` in API call | Stripe API requirement |
| Tool permissions | **exec** with script path (2026.3.x) or acpx runtime | Agent must run script in correct context |
| Secret leakage | `.env` + `dotenv`, gitignored | Security compliance |

**OpenClaw 2026.3.x:** Custom tools in `openclaw.json` are not supported. Use **exec** to run `node .../canton/create-stripe-link.js`; do not add `create_stripe_payment_link` under `tools`.

---

## Step-by-Step Implementation

*(Replace `YOUR_AGENT` and paths with your agent id and workspace.)*

### 1. Install Dependencies

```bash
cd /path/to/agent/workspace
npm install stripe dotenv
```

### 2. Payment Script

Use `canton/create-stripe-link.js` in this repo. It loads `.env` from repo root, uses the Stripe SDK, and includes `quantity: 1`. Accepts `--price` or `--amount` (cents), `--currency`, `--description`.

### 3. Secure Credentials

```bash
echo "STRIPE_SECRET_KEY=sk_test_..." >> .env
echo ".env" >> .gitignore   # SECURITY MANDATORY
```

Never commit real keys.

### 4. OpenClaw (2026.3.x: use exec)

**Do not** add a `tools.create_stripe_payment_link` block in `openclaw.json` — it causes "Unrecognized key". Have the agent use the **exec** tool:

```bash
node /path/to/KrumpPhysio/canton/create-stripe-link.js --price {amount} --description "{description}"
```

Set `cwd` to the repo root if needed. See [agent/IDENTITY.md](../agent/IDENTITY.md) and [STRIPE.md](STRIPE.md).

### 5. ACP Runtime (when using sessions_spawn)

```bash
npm install -g @openclawd/acpx   # one-time
```

In `openclaw.json` plugins:

```json
"acpx": {
  "enabled": true,
  "config": { "defaultAgent": "YOUR_AGENT" }
}
```

Add `acpx` to `plugins.allow`.

### 6. Restart Gateway

```bash
openclaw gateway restart
```

---

## Verification Checklist (<2 min)

1. **Manual test**
   ```bash
   node canton/create-stripe-link.js --price 1000 --description "Test"
   # Expected: {"url":"https://buy.stripe.com/...","id":"plink_..."}
   ```

2. **OpenClaw test** (if using ACP spawn)
   ```bash
   openclaw sessions spawn --runtime acp --agent YOUR_AGENT --task "Create $10 link" --model flock-qwen-thinking
   ```

3. **Stripe validation**
   ```bash
   curl -sI $(node canton/create-stripe-link.js --price 100 --currency usd --description x | jq -r .url) | grep HTTP
   # Expected: HTTP/2 200
   ```

---

## Critical Notes

- Use **`--price`** (or `--amount`) in the exec command for amount in cents.
- **Always** include `quantity: 1` in the Stripe API call (script does this).
- **Never** hardcode keys; keep `.env` gitignored.
- When spawning: use **`--runtime acp`** if your setup uses ACP.

---

## Pro Tips

1. **Parameter pattern** for payment tools: `amount` (cents), `currency`, `description`.
2. **Observability** in `openclaw.json`: `anyway-openclaw` with `captureToolIO: true`.
3. **Error handling**: script exits with code 1 and JSON error on failure; ensure `STRIPE_SECRET_KEY` is set.

---

## See also

- [STRIPE.md](STRIPE.md) — Setup and usage
- [STRIPE-INTEGRATION-FIX-PROTOCOL.md](STRIPE-INTEGRATION-FIX-PROTOCOL.md) — Full protocol (ACP, pitfalls, verification)
