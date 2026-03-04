# KrumpPhysio — Pitch deck content (for Lovable)

Use this content for each slide. Copy into Lovable or your deck tool. Bounty-friendly: problem, solution, technical implementation, bounty partner integration.

---

## Slide 1 — Title

**KrumpPhysio**  
*AI physiotherapy coach that speaks Krump*

UK AI Agent Hackathon EP4 × OpenClaw · FLock Track · Anyway Bounty

---

## Slide 2 — The problem

**Rehab is boring. Patients drop off.**

- Prescribed exercises feel like chores → low adherence
- Clinics can’t see what happens at home → no visibility
- No engaging, culturally grounded way to keep people moving

**Impact:** Poor adherence to rehab and cardio worsens non-communicable disease outcomes (SDG 3.4).

---

## Slide 3 — Our solution

**KrumpPhysio: rehab as battle rounds.**

- **AI coach** that scores form and range of motion, gives feedback in **Krump** vocabulary and **Laban** notation
- **Telegram** — patients message the agent like a coach
- **Auditable** — optional session logs on a **Canton (Daml)** ledger
- **Monetizable** — **Anyway** for observability, **Stripe** for fiat payments

**One line:** Turn daily physio into Krump-style battle rounds so people stick with it.

---

## Slide 4 — How it works (user flow)

1. **Patient** sends angles or a request on Telegram (e.g. “Score my right shoulder: target 90°, observed 88°, round 1”).
2. **OpenClaw agent** (KrumpPhysio) uses **FLock** to reason and reply with a score /10, form feedback, and Laban notation.
3. **Optional:** Agent logs the session to **Canton** via a script for tamper-evident history.
4. **Operator** sees traces and cost in **Anyway**; can charge via **Stripe** payment links.

---

## Slide 5 — Technical implementation (architecture)

**Tech stack**

| Layer | Technology |
|-------|------------|
| Agent runtime | **OpenClaw** |
| LLM | **FLock** (Qwen 235B Thinking, etc.) |
| Channel | **Telegram** |
| Scoring | Node.js `score.js` (angles → score + feedback) |
| Ledger | **Canton** (Daml `SessionLog` contracts) |
| Observability | **Anyway** (Traceloop / OpenClaw plugin) |
| Payments | **Stripe** (Node SDK, payment links; no CLI) |

**Design:** Agent decides when to score and when to log to Canton; operator gets full observability and can monetize via Stripe.

---

## Slide 6 — Bounty partner integration (FLock)

**FLock as the only LLM in the judging path**

- All agent reasoning and replies use **FLock** models (e.g. `qwen3-235b-a22b-thinking-2507`).
- No OpenAI/Anthropic in production path.
- Configured in OpenClaw as sole provider for KrumpPhysio (and other agents in our setup).

**Why it matters:** Open-weight models, hackathon-compliant, scalable for physio coaching.

---

## Slide 7 — Bounty partner integration (Anyway)

**Anyway: observability, not payments**

- **Traces** — Every session and tool call visible in the Anyway dashboard.
- **Cost** — Token usage and run cost so operators can tune and budget.
- **Integration:** OpenClaw plugin `@anyway-sh/anyway-openclaw` + optional Python tracer around scoring.
- **Stripe** is used separately for fiat payments; Anyway = measure and prove, Stripe = get paid.

**Result:** Full visibility into agent behavior and cost for a paid physio offering.

---

## Slide 8 — Bounty partner integration (Stripe)

**Stripe: fiat payments for the agent**

- **Payment links** created via **Node.js script** + Stripe SDK (no Stripe CLI).
- `STRIPE_SECRET_KEY` in `.env`; script uses `quantity: 1` and correct API params (documented in repo).
- **Test product link:** KrumpPhysio Session £5/month (sandbox).
- **Docs in repo:** Setup, integration fix, full protocol, 5-minute quickstart for other agents.

**Eligibility:** Commercialization via product link (Stripe) + observability (Anyway) + FLock-only agent.

---

## Slide 9 — OpenClaw & multi-channel

**OpenClaw as core runtime**

- **Agents:** KrumpPhysio (krumpbot-fit) and others; identity, SOUL, tools (exec, read, edit, etc.).
- **Multi-channel:** **Telegram** (group + DM) bound to the agent; gateway handles routing.
- **Canton logging:** Agent uses **exec** to run `log-session.js` when it decides a session should be on-ledger (OpenClaw 2026.3.x: no custom tool definitions; exec is the supported pattern).

---

## Slide 10 — SDG alignment & impact

**SDG 3 — Good health and well-being**

- **Target 3.4** — Reduce premature mortality from non-communicable diseases.
- **How:** Rehab and cardio adherence through **gamified Krump movement** and an AI coach that speaks the user’s language (Krump + Laban).
- **Measurable:** Movement scores, optional on-ledger session logs, engagement via Telegram.

**Impact:** Rehab that feels like battle rounds, not paperwork — so people stick with it.

---

## Slide 11 — Demo / live (placeholder)

**Live demo**

- Open **Telegram** → message KrumpPhysio with a scoring request (e.g. angles + round).
- Show **reply** (score /10, feedback, Laban, “Krump for life!”).
- Optional: show **Canton** Navigator or `summary.js` for session logs; **Anyway** dashboard for traces; **Stripe** test link.

*Use this slide for screen share or embedded short clip.*

---

## Slide 12 — Repo & resources

**Public GitHub**

- **Repo:** [github.com/arunnadarasa/krumpphysio](https://github.com/arunnadarasa/krumpphysio)
- **README:** Overview, setup, Canton, Anyway & Stripe, ClawHub skill.
- **Docs:** Implementation guide (FLock + OpenClaw + Canton), Stripe setup & integration fix protocol, web search (Kimi), OpenClaw tools.

**ClawHub skill:** Other OpenClaw agents can install the KrumpPhysio coaching pattern.

---

## Slide 13 — Thank you / contact

**KrumpPhysio**  
Rehab as battle rounds. SDG 3. FLock · OpenClaw · Anyway · Stripe.

- **Repo:** [github.com/arunnadarasa/krumpphysio](https://github.com/arunnadarasa/krumpphysio)
- **Test product link:** [buy.stripe.com/test_...](https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00) (KrumpPhysio Session £5/month)

*Add your contact / team / social here.*

---

## Bounty checklist (for your reference)

- [ ] **Pitch/demo video (5–10 min):** Problem, solution, technical implementation, bounty integration, short live demo.
- [ ] **Public GitHub repo:** README with overview, setup, architecture, bounty-specific integration.
- [ ] **Pitch deck (optional):** This content in Lovable or your preferred tool.
