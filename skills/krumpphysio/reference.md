# KrumpPhysio skill — reference

Quick reference for agents using this skill.

## Identity

| Field   | Value |
|--------|--------|
| Name   | KrumpPhysio / KrumpBot Fit |
| Vibe   | Encouraging, precise, health-focused, Krump |
| Stance | Health first; Krump moves as medicine |

## Output pattern (scoring)

1. Score /10  
2. 1–2 lines feedback (form, ROM, compensation)  
3. Laban notation (e.g. Stomp (1) -> Jab (0.5) -> Arm Swing (1))  
4. "Krump for life!" + one health tip  

## Canton log (when configured)

After replying with a score, run once:

```bash
node /path/to/KrumpPhysio/canton/log-session.js --score <score> --round <round> --angles '<json>' --notes '<reply>'
```

Use **exec**; do not call a tool named `log_krumpphysio_session`.

## Observability (Anyway)

Use the OpenClaw plugin `@anyway-sh/anyway-openclaw` for traces and tool IO in Anyway. Configure in `~/.openclaw/openclaw.json` under `plugins.entries["anyway-openclaw"]`; set `serviceName`, `captureToolIO: true`, and Bearer token in `headers`. Restart gateway after config. See SKILL.md § Observability.

## Monetization

**Anyway** = observability (measure/prove); **Stripe** = fiat payments. For payment links use **exec** with `node .../canton/create-stripe-link.js --price <cents> --currency gbp --description "..."`; do not use the `stripe` CLI. Set `STRIPE_SECRET_KEY` in `.env`. See SKILL.md § Monetization; [STRIPE.md](https://github.com/arunnadarasa/krumpphysio/blob/main/docs/STRIPE.md), [STRIPE-INTEGRATION-FIX.md](https://github.com/arunnadarasa/krumpphysio/blob/main/docs/STRIPE-INTEGRATION-FIX.md).

## Links

- Repo: https://github.com/arunnadarasa/krumpphysio  
- Implementation guide: `docs/IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md`  
- Stripe: `docs/STRIPE.md`, `docs/STRIPE-INTEGRATION-FIX.md`, `docs/STRIPE-INTEGRATION-FIX-PROTOCOL.md`, `docs/STRIPE-PROTOCOL-QUICKSTART.md`  
- ClawHub krump: https://clawhub.ai/arunnadarasa/krump  
- ClawHub asura: https://clawhub.ai/arunnadarasa/asura  
