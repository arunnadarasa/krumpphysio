# Stripe setup (payment links)

KrumpPhysio can create payment links via the Stripe API. No Stripe CLI is required for creating links.

## Required

1. **Stripe API key** — Set in `.env` (copy from [.env.example](../.env.example)):
   ```bash
   STRIPE_SECRET_KEY=sk_test_...   # or sk_live_... for production
   ```
   Get keys from [Stripe Dashboard → Developers → API keys](https://dashboard.stripe.com/apikeys).

2. **Script in this repo** — `canton/create-stripe-link.js`  
   Creates a one-off payment link using the API. Run from repo root or with absolute path:
   ```bash
   node canton/create-stripe-link.js --amount 500 --currency gbp --description "KrumpPhysio Session"
   ```
   Outputs JSON: `{ "url": "https://buy.stripe.com/...", "id": "plink_..." }`.

## Optional

- **Stripe CLI** — Only needed for local webhook testing (e.g. `stripe listen --forward-to localhost:...`). Install: `brew install stripe/stripe-cli/stripe`. Not required for payment link creation.
- **STRIPE_WEBHOOK_SECRET** — Set in `.env` if you use Stripe webhooks (e.g. for subscription events).

## Pre-made test link

For demos and the Anyway bounty, use the existing test product link (README):  
https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00 (KrumpPhysio Session, £5/month).

## Agent / exec

If the agent is asked to “create a payment link”, it can run the script via **exec** (OpenClaw does not support custom tools in config; use exec with the path to `canton/create-stripe-link.js`). Ensure `STRIPE_SECRET_KEY` is set in `.env` on the machine where the agent runs.
