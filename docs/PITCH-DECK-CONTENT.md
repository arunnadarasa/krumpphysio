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
- **Telegram** — patients message the agent; **exec** runs on both Chat and Telegram when KrumpPhysio is default (quantum plan, Stripe, Canton)
- **Video sidecar bot** — patients upload short rehab clips to a dedicated Telegram video bot. **`/start`** welcomes users with a full command list and optionally asks for name, interest, and limbs to work on. The bot runs MediaPipe locally, replies with a KrumpPhysio-style score/smoothness/Laban summary, and forwards structured metrics into OpenClaw so KrumpPhysio can still decide about Canton logging and Stripe. With **Kimi + Replicate**, the bot can send KrumpGotchi media with Kimi’s descriptions and **AI-generated** exercise images and short videos (`/kimi_gen_image`, `/kimi_gen_video`).
- **Quantum-inspired plans** — Guppy + Selene script → weekly focus and intensity; agent replies with short coaching message (not raw JSON)
- **Auditable** — optional session logs on a **Canton (Daml)** ledger
- **Monetizable** — **Anyway** for observability, **Stripe** for fiat payments
- **Voice + music (optional)** — ElevenLabs TTS/STT gives patients voice notes and voice-driven captions on Telegram; when ElevenLabs Music is available the bot can also send a short instrumental beat after analysis, but the core experience (text + voice + Canton/Stripe/Anyway) works without Music.
- **Privacy & trust** — Video stays on the server; only metrics (+ optional ZKP) go to the coach. `/privacy` in the bot; optional auto-delete of video; OpenClaw messages tagged with privacy headers. See [PRIVACY.md](PRIVACY.md) and [PRIVACY-HEALTH-AUTHORITY-SUMMARY.md](PRIVACY-HEALTH-AUTHORITY-SUMMARY.md).

**One line:** Turn daily physio into Krump-style battle rounds so people stick with it.

---

## Slide 4 — How it works (user flow)

1. **Patient** opens the video bot and gets **`/start`** — a welcome with command list and optional ask for name, interest, and limbs. They then send either:
   - joint angles (text) on Telegram, or  
   - a **short video clip** with a caption like `/analyze left_knee 90` to the video bot, or  
   - **`/kimi_gen_image`** or **`/kimi_gen_video`** for AI-generated exercise media (Kimi + Replicate).
2. **Video path:** MediaPipe-based sidecar analyses the clip, replies with a KrumpPhysio-style score and summary, and forwards structured metrics (joint, target, observed, smoothness) into OpenClaw via the **OpenResponses HTTP API** so KrumpPhysio can decide about Canton logging and payments.
3. **Direct text path:** KrumpPhysio uses **FLock** to reason and reply with a score /10, form feedback, and Laban notation.
4. **Optional:** Agent logs the session to **Canton** via a script for tamper-evident history (tested end‑to‑end with full cryptographic party IDs and JWT).
5. **Operator** sees traces and cost in **Anyway**; can charge via **Stripe** payment links.

---

## Slide 5 — Technical implementation (architecture)

**Tech stack**

| Layer | Technology |
|-------|------------|
| Agent runtime | **OpenClaw** |
| LLM | **FLock** (Qwen 235B Thinking, etc.) |
| Channel | **Telegram** (KrumpPhysio agent) + separate **video bot** |
| Scoring | Node.js `score.js` (angles → score + feedback) |
| Video analysis | Python + **MediaPipe** (`video/analyse_movement.py`, `.venv-video`) |
| Generated media (video bot) | **FLock (Kimi)** + **Replicate** (FLUX image, minimax/video-01) for `/kimi_gen_image`, `/kimi_gen_video` |
| Ledger | **Canton** (Daml `SessionLog` contracts) |
| Observability | **Anyway** (Traceloop / OpenClaw plugin) |
| Payments | **Stripe** (Node SDK, payment links; no CLI) |
| Quantum (optional) | **Guppy + Selene** (quantum-inspired weekly focus/intensity; exec on Chat + Telegram) |
| Verifiable input (optional) | **Sindri** (ZKP: attest video-bot payload to OpenClaw/FLock without exposing video or identity) |

**Design:** Agent decides when to score and when to log to Canton; a sidecar video bot handles raw Telegram uploads and forwards structured metrics into OpenClaw via the OpenResponses API. Operator gets full observability and can monetize via Stripe. KrumpPhysio as default agent so exec (quantum, Stripe, Canton) runs on both Chat and Telegram.

---

## Slide 6 — Bounty partner integration (FLock)

**FLock as the only LLM in the judging path**

- All agent reasoning and replies use **FLock** models (e.g. `qwen3-235b-a22b-thinking-2507`).
- No OpenAI/Anthropic in production path.
- Configured in OpenClaw as sole provider for KrumpPhysio (and other agents in our setup).

**Why it matters:** Open-weight models, hackathon-compliant, scalable for physio coaching.

---

## Slide 6b — ZKP (Sindri): verifiable inputs for trust

**What it does**

- The video bot sends only **metrics** (joint, angles, smoothness) to OpenClaw/FLock — never the video.
- With **Sindri** we attach a **zero-knowledge attestation** (commitment or proof) so the input to the coach agent is **verifiable**: “this summary came from a real analysis” — without exposing the video or the patient.

**Value for the submission**

- **Trust:** Patients and health authorities see that the AI acts on **provable** data, not assumed or fake inputs.
- **Privacy:** Prove correctness without sending video or identifiers; supports our privacy/compliance story.
- **Anyway + ZKP:** Anyway = “measure and prove what happened”; ZKP = “prove the **input** was correct.” Together they strengthen the “prove it” narrative.
- **Differentiation:** Few projects add ZK proofs into the agent pipeline; we show it’s feasible with OpenClaw + FLock.

**One line:** “Verifiable inputs — we prove the coach is acting on real video analysis without sending video or identity to the LLM.”

(See [ZKP-SINDRI-HACKATHON-VALUE.md](ZKP-SINDRI-HACKATHON-VALUE.md) for full benefits and demo tips.)

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

- **Agents:** KrumpPhysio (krumpbot-fit) as **default** (first in `agents.list`) so Chat and Telegram both use it; identity, SOUL, tools (exec, read, edit, etc.).
- **Multi-channel:** **Telegram** (group + DM) bound to krumpbot-fit; **exec** runs on both Chat and Telegram (quantum script, Stripe, Canton) when KrumpPhysio is default.
- **Best practices:** Paste instruction first to lock exec + comprehensive reply; reply format = focus + intensity + tip + “Krump for life!” + health tip (see repo BEST-PRACTICES.md).
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

- Open **Telegram**:
  - Path 1: message KrumpPhysio with “Give me a quantum-inspired exercise plan” or a scoring request (e.g. angles + round).  
  - Path 2: open the **KrumpPhysio video bot** — `/start` for welcome and command list — then send a short video clip with caption `/analyze left_knee 90`, or try `/kimi_gen_image` / `/kimi_gen_video` for AI-generated exercise media.
- Show **replies**:
  - Quantum: focus + intensity + tip + “Krump for life!”.  
  - Video: score /10, smoothness, Laban, “Krump for life!” from the video bot, plus KrumpPhysio’s follow‑up via OpenClaw if desired.
- Optional: show **Canton** Navigator or `summary.js` for session logs; **Anyway** dashboard for traces (including OpenResponses), **Stripe** test link; **ZKP:** run `python video/check_sindri_proofs.py` to show recent proofs (verifiable input).

*Use this slide for screen share or embedded short clip.*

---

## Slide 12 — Repo & resources

**Public GitHub**

- **Repo:** [github.com/arunnadarasa/krumpphysio](https://github.com/arunnadarasa/krumpphysio)
- **README:** Overview, setup, Canton, Anyway & Stripe, ClawHub skill.
- **Docs:** Implementation guide (FLock + OpenClaw + Canton), Stripe setup & integration fix protocol, web search (Kimi), OpenClaw tools, **best practices** (default agent, paste instruction, comprehensive quantum reply), **Privacy** (PRIVACY.md, PRIVACY-HEALTH-AUTHORITY-SUMMARY.md), **ZKP** (SINDRI-ZKP-TELEGRAM-FLOCK.md, ZKP-SINDRI-HACKATHON-VALUE.md).

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
