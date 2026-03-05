# Stripe Integration Fix Guide

## Problem Summary

Multiple issues prevented successful Stripe payment link generation:

1. CLI command syntax error (`payment-links` vs `payment_links`)
2. Missing Stripe Node.js module
3. Unconfigured environment variables
4. Missing `quantity` parameter in API call
5. Incorrect tool flag mapping (`--amount` vs `--price`)
6. **Wrong Stripe account / key** – using a different Stripe test account to the one expected (e.g. personal test account vs the dedicated **“Anyway US sandbox”** account) meant links and payments showed up in a different dashboard, which looked like “no payments” even though the script was working.

## Step-by-Step Fix

### 1. Switch to Stripe Node.js Library (Critical Fix)

**Problem**: CLI command syntax errors and version conflicts  
**Solution**: Replace CLI with Stripe SDK (more reliable)

The script `canton/create-stripe-link.js` uses the Stripe Node.js SDK:

```javascript
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const paymentLink = await stripe.paymentLinks.create({
  line_items: [{ price_data: { ... }, quantity: 1 }]
});
```

### 2. Install Required Dependencies

```bash
cd /Users/openclaw/Documents/KrumpPhysio
npm install stripe dotenv
```

### 3. Configure Environment Variables

**Create or edit `.env`** in the repo root (never commit real keys):

```bash
STRIPE_SECRET_KEY=sk_test_...   # or sk_live_... for production
```

Get keys from [Stripe Dashboard → API keys](https://dashboard.stripe.com/apikeys).

**Use the correct Stripe account:** For the Anyway bounty we use a dedicated **“Anyway US sandbox”** Stripe account. Make sure the secret key you paste into `.env` comes from that sandbox (not from a different Stripe account), and complete any basic verification steps Stripe asks for in the dashboard so the sandbox behaves as expected.

The script loads `.env` via `dotenv` (from repo root when run from the project).

### 4. Fix API Parameters

**Problem**: Missing required `quantity` parameter  
**Solution**: The script explicitly sets `quantity: 1` in the payment link request.

### 5. OpenClaw Tool Configuration

OpenClaw 2026.3.x does not support custom tools in `openclaw.json`. Use the **exec** tool instead. The agent should run:

```bash
node /path/to/KrumpPhysio/canton/create-stripe-link.js --price <cents> --currency gbp --description "..."
```

The script accepts both `--amount` and `--price` for the amount in cents.

### 6. Verify Anyway Observability

Ensure plugin configuration captures tool I/O:

```json
"plugins": {
  "entries": {
    "anyway-openclaw": {
      "config": {
        "captureToolIO": true,
        "serviceName": "krumpbot-fit"
      }
    }
  }
}
```

## Validation Steps

1. **Manual test**:

   ```bash
   cd /Users/openclaw/Documents/KrumpPhysio
   node canton/create-stripe-link.js --price 1000 --currency usd --description "KrumpPhysio session"
   # Expected output: {"url":"https://buy.stripe.com/...","id":"plink_..."}
   ```

2. **Stripe verification**:

   ```bash
   curl -sI $(node canton/create-stripe-link.js --price 100 --currency usd --description test | jq -r .url) | grep HTTP
   # Should return: HTTP/2 200
   ```

3. **Anyway trace check**  
   In the Anyway dashboard: `service.name = "krumpbot-fit"` and look for exec/tool spans that run the script.

## Key Improvements

- Eliminated CLI version conflicts by using Stripe SDK
- Secure environment variable handling via `.env` and `dotenv`
- Fixed critical API parameter requirements (`quantity: 1`)
- Full observability in Anyway when `captureToolIO: true`
- Script accepts both `--amount` and `--price` for compatibility

## See also

- [STRIPE.md](STRIPE.md) — Setup and usage
- [STRIPE-INTEGRATION-FIX-PROTOCOL.md](STRIPE-INTEGRATION-FIX-PROTOCOL.md) — Full protocol (ACP, verification, pitfalls)
- [STRIPE-PROTOCOL-QUICKSTART.md](STRIPE-PROTOCOL-QUICKSTART.md) — 5-minute quick setup
- [README.md](../README.md) — Test product link and optional Stripe section
