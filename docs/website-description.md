# KrumpPhysio — Website & product description

Use this text for the Lovable (or other) marketing site, app store copy, and pitch decks.

---

## Elevator pitch

**KrumpPhysio** (KrumpBot Fit) is an AI physiotherapy and movement coach that speaks in **Krump** — turning rehab into battle rounds, scoring your form and range of motion, and optionally logging sessions to an auditable ledger. Patients chat on **Telegram**; clinics and operators get **observability** (Anyway) and can **get paid in fiat** (Stripe) when offering physiotherapy through the OpenClaw agent.

---

## Business model: observability + fiat payments

Two pillars support **OpenClaw agents getting paid when they offer physiotherapy to patients**:

1. **Anyway (observability)**  
   - **Does not** process payments.  
   - Provides **traces, token usage, and cost visibility** for every session and tool call.  
   - Enables **trust, tuning, and cost control**: you see what the agent did and what it cost (LLM + tools).  
   - Use the OpenClaw plugin `@anyway-sh/anyway-openclaw` and/or the Python tracer around `score.js` so sessions show up in the Anyway dashboard.

2. **Stripe (fiat payments)**  
   - **Enables** charging in fiat: subscriptions, per-session fees, clinic billing.  
   - Set `STRIPE_SECRET_KEY` in `.env`; payment links are created via a **Node.js script** (Stripe SDK), not the Stripe CLI.  
   - The operator or platform charges patients or clinics; the OpenClaw physiotherapy agent is the service being monetized.  
   - **Test product link (sandbox):** [KrumpPhysio Session — £5/month](https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00).

**Summary:** Anyway = *measure and prove what happened*; Stripe = *get paid for it*. Together they support a paid physiotherapy offering powered by OpenClaw.

---

## Who it’s for

- **Physiotherapists & rehab clinics** — Digital coach that scores form, tracks progress, and keeps patients motivated between visits.
- **Health & fitness builders** — SDG 3–aligned product with a ready-made coaching pattern and audit trail.
- **Movement & dance communities** — Authentic Krump energy in safe, injury-aware coaching.

---

## What it does

- **Movement & ROM scoring** — Joint angles in → score out of 10, feedback, and Laban-style notation.
- **Telegram coaching** — Patients message the agent; responses use Krump vocabulary and health-first advice.
- **Canton session logs** — Optional tamper-evident `SessionLog` contracts on a Daml ledger for auditability.
- **Observability (Anyway)** — Traces and tool IO so you can debug, tune, and control cost.
- **Stripe payment links** — Create one-off or product links via `canton/create-stripe-link.js` (Stripe Node SDK; no CLI required). Full integration fix protocol and 5-minute quickstart in the repo.
- **Web search (optional)** — When configured (e.g. Kimi), the agent can use web search for up-to-date info.
- **Reusable skill** — ClawHub skill so other OpenClaw agents can adopt the same coaching pattern.

---

## Tech stack (one line)

OpenClaw + FLock + Telegram + Node scoring engine + Canton (Daml) + Anyway (observability) + Stripe (payments via Node SDK) + optional Kimi/web search.

---

## Links

- **Repo:** https://github.com/arunnadarasa/krumpphysio  
- **Stripe product link (test):** https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00 (KrumpPhysio Session, £5/month)  
- **Implementation guide:** [IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md](IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md)  
- **Stripe:** [STRIPE.md](STRIPE.md), [STRIPE-INTEGRATION-FIX.md](STRIPE-INTEGRATION-FIX.md), [STRIPE-INTEGRATION-FIX-PROTOCOL.md](STRIPE-INTEGRATION-FIX-PROTOCOL.md), [STRIPE-PROTOCOL-QUICKSTART.md](STRIPE-PROTOCOL-QUICKSTART.md)  
- **ClawHub skill:** [skills/krumpphysio/](../skills/krumpphysio/)

---

## For implementers (docs in repo)

| Topic | Doc |
|-------|-----|
| Full stack setup | [IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md](IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md) |
| Stripe setup & payment links | [STRIPE.md](STRIPE.md) |
| Stripe integration fix (SDK, quantity, env) | [STRIPE-INTEGRATION-FIX.md](STRIPE-INTEGRATION-FIX.md) |
| Stripe full protocol (ACP, verification, pitfalls) | [STRIPE-INTEGRATION-FIX-PROTOCOL.md](STRIPE-INTEGRATION-FIX-PROTOCOL.md) |
| Stripe 5-minute quickstart | [STRIPE-PROTOCOL-QUICKSTART.md](STRIPE-PROTOCOL-QUICKSTART.md) |
| OpenClaw web search (Kimi, etc.) | [OPENCLAW-WEB-SEARCH.md](OPENCLAW-WEB-SEARCH.md) |
| OpenClaw edit tool (old_string / new_string) | [OPENCLAW-TOOLS.md](OPENCLAW-TOOLS.md) |
| Canton + Telegram test run | [canton-telegram-test-run.md](canton-telegram-test-run.md) |
