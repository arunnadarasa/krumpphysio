# KrumpPhysio

AI krump-inspired physiotherapy coach for the **UK AI Agent Hackathon EP4 x OpenClaw**.

---

## 1. Project overview

- **Goal:** Support **SDG 3 – Good Health and Well-being** (Target 3.4: reduce premature mortality from non-communicable diseases) by helping people stick to rehab and cardio through gamified Krump movement.
- **Concept:** Turn daily physiotherapy and cardio into Krump-style “battle rounds.” The agent scores form, range of motion, and consistency, then frames feedback with Krump vocabulary and Laban-style notation to keep motivation high.
- **What it does:** Patients chat on **Telegram** (text or voice) or upload short **video clips**; the agent returns scores out of 10, form feedback, and “Krump for life!” tips. Optional: **quantum-inspired** weekly exercise plans (Guppy + Selene), **auditable session logs** (Canton/Daml), **observability** (Anyway), and **fiat payments** (Stripe). The **Telegram video sidecar bot** welcomes users with **`/start`** (command list + optional ask for name, interest, limbs), runs local MediaPipe pose analysis, and can send **voice notes** (ElevenLabs TTS) for accessibility. With **Kimi (FLock)** and **Replicate**, the bot can send KrumpGotchi media with AI descriptions and **AI-generated** exercise images and short videos (`/kimi_gen_image`, `/kimi_gen_video`).

---

## 2. Setup & installation

### Prerequisites

- **Node.js** (v18+) for scoring and Canton/Stripe scripts  
- **Python 3.10+** for quantum (Guppy/Selene) and video bot (MediaPipe, ElevenLabs)  
- **Java 17** for Daml/Canton (optional; only if using on-ledger session logs)

### Core setup

1. **Clone and env**
   ```bash
   git clone https://github.com/arunnadarasa/krumpphysio.git && cd krumpphysio
   cp .env.example .env   # edit with your keys; never commit .env
   ```

2. **OpenClaw + FLock**
   - Install OpenClaw and configure FLock as the LLM provider (see [docs/IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md](docs/IMPLEMENTATION-GUIDE-FLOCK-OPENCLAW-CANTON.md)).
   - Point the KrumpPhysio agent workspace to this repo (or a copy). Set **krumpbot-fit** first in `agents.list` so Chat and Telegram use it by default.

3. **Scoring**
   - From repo root: `node score.js '[{"joint":"left_shoulder","target":120,"observed":118}]' 1`  
   - Scoring is also triggered by the agent via **exec** when users send angles in Chat or Telegram.

### Optional: Canton (on-ledger session logs)

1. Start the ledger (from your Daml project):
   ```bash
   cd /path/to/krumpphysio-daml
   daml start
   ```
2. In this repo’s `.env`: `CANTON_ENABLE=true`, party IDs, JWT, template ID. See [canton/CANTON.md](canton/CANTON.md).
3. After the agent gives a score, it can run `node canton/log-session.js ...` via exec to create a `SessionLog` contract. View with `node canton/summary.js` or Daml Navigator.

### Optional: Telegram video bot (MediaPipe + ElevenLabs)

```bash
python3.11 -m venv .venv-video && source .venv-video/bin/activate
pip install -r video/requirements.txt
export KRUMP_VIDEO_BOT_TOKEN="<your bot token>"
export OPENCLAW_GATEWAY_TOKEN="<gateway token>"
# Optional: ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (required for TTS; use a voice ID from your ElevenLabs account)
# Optional Kimi + Replicate: FLOCK_API_KEY (platform.flock.io), REPLICATE_API_TOKEN (for /kimi_image, /kimi_video, /kimi_gen_image, /kimi_gen_video)
# Optional ZKP: SINDRI_API_KEY (attest payload to OpenClaw); SINDRI_ATTESTATION_CIRCUIT_ID (for full proof)
# Optional privacy: KRUMP_VIDEO_DELETE_AFTER_ANALYSIS=1 (delete each video after analysis)
# Optional KrumpGotchi: LINK_WEBSITE_URL=https://your-krumpgotchi-site.com (shown in /link reply)
python video/telegram_bot.py
```

**Video bot commands:** `/start` — welcome + command list + optional ask for name, interest, limbs to work on. `/help` — same as start. `/privacy` — privacy notice. `/link` — link Telegram to KrumpGotchi (if `LINK_WEBSITE_URL` set). `/exercise_demo` — KrumpGotchi avatar + sample video. `/kimi_image`, `/kimi_video` — KrumpGotchi media with Kimi’s description (requires `FLOCK_API_KEY`). `/kimi_gen_image`, `/kimi_gen_video` — AI-generated exercise image/video via Kimi + Replicate (requires `FLOCK_API_KEY` and `REPLICATE_API_TOKEN`). Send a video with caption e.g. `/analyze left_knee 90` for pose analysis.

**Link Telegram (KrumpGotchi):** Users can send `/link` to the bot to get a one-time code and link their Telegram to the KrumpGotchi website. Set `LINK_WEBSITE_URL` to your web app URL. Run the link verify API so the website can validate codes: `python video/link_api.py` (default port 8765; set `LINK_API_PORT` if needed). Bot and API must share the same repo (so they share `data/telegram_link_codes.json`). See [docs/LOVABLE-KRUMPGOTCHI-PROMPT.md](docs/LOVABLE-KRUMPGOTCHI-PROMPT.md) for the Lovable prompt to build the website.

Optional **ZKP (Sindri):** If `SINDRI_API_KEY` is set, the video bot attests the payload sent to OpenClaw (commitment or full proof when `SINDRI_ATTESTATION_CIRCUIT_ID` is set). See [docs/SINDRI-ZKP-TELEGRAM-FLOCK.md](docs/SINDRI-ZKP-TELEGRAM-FLOCK.md).

**Privacy:** For patient and health-authority confidence, see [docs/PRIVACY.md](docs/PRIVACY.md) and the one-page [docs/PRIVACY-HEALTH-AUTHORITY-SUMMARY.md](docs/PRIVACY-HEALTH-AUTHORITY-SUMMARY.md) (UK/ICO and GDPR). The bot supports `/privacy` and optional auto-deletion of video after analysis (`KRUMP_VIDEO_DELETE_AFTER_ANALYSIS=1`). Messages to OpenClaw/FLock include privacy headers (`X-KrumpPhysio-Source`, `X-KrumpPhysio-Privacy`) for a minimal-PII layer.

### Optional: Quantum (Guppy + Selene)

```bash
python3.11 -m venv .venv-quantum && source .venv-quantum/bin/activate
pip install -r quantum/requirements.txt
python quantum/optimise_exercises.py --shots 5
```

The agent runs this via **exec** when the user asks for a “quantum-inspired exercise plan.” See [quantum/README.md](quantum/README.md) and [docs/BEST-PRACTICES.md](docs/BEST-PRACTICES.md).

### Optional: Anyway & Stripe

- **Anyway:** Set `ANYWAY_API_KEY`; use the OpenClaw plugin `@anyway-sh/anyway-openclaw` (and optionally the Python tracer). Sandbox: `https://trace-dev-collector.anyway.sh/`.
- **Stripe:** Set `STRIPE_SECRET_KEY` (use the **Anyway US sandbox** Stripe account for the bounty). Create links with `node canton/create-stripe-link.js --amount <cents> --currency gbp --description "..."`. See [docs/STRIPE-INTEGRATION-FIX.md](docs/STRIPE-INTEGRATION-FIX.md).

---

## 3. Architecture overview (tech stack / system design)

| Layer            | Technology |
|------------------|------------|
| Agent runtime    | **OpenClaw** |
| LLM              | **FLock** (e.g. Qwen 3 235B Thinking) |
| Channel          | **Telegram** (KrumpPhysio agent) + separate **video sidecar bot** |
| Scoring          | Node.js `score.js` (angles → score + feedback) |
| Video analysis   | Python + **MediaPipe** (`video/analyse_movement.py`, `.venv-video`) |
| Generated media (video bot) | **FLock (Kimi)** + **Replicate** (FLUX image, minimax/video-01) for `/kimi_gen_image`, `/kimi_gen_video` |
| Ledger           | **Canton** (Daml `SessionLog` contracts) |
| Observability    | **Anyway** (OpenClaw plugin + optional Python tracer) |
| Payments         | **Stripe** (Node SDK, payment links) |
| Voice / music    | **ElevenLabs** (TTS/STT/music in video bot only) |
| Quantum (opt.)   | **Guppy + Selene** (quantum-inspired weekly focus/intensity via exec) |
| ZKP (opt.)       | **Sindri** (attest Telegram → OpenClaw payload for verifiable FLock input) |

**Design:** The **agent** (FLock) decides when to score and when to log to Canton. A **Telegram video sidecar bot** accepts video uploads, runs MediaPipe locally, replies with a KrumpPhysio-style summary (and optional voice note), and forwards structured metrics to OpenClaw via the **OpenResponses HTTP API** so the agent can still trigger Canton logging and Stripe/Anyway flows. KrumpPhysio as the **default agent** ensures **exec** (quantum script, Stripe link, Canton log) runs on both OpenClaw Chat and Telegram.

---

## 4. Bounty-specific integration

- **FLock (LLM):** All agent reasoning and replies use **FLock** models (e.g. `qwen3-235b-a22b-thinking-2507`). No OpenAI/Anthropic in the production path. Configured in OpenClaw as the provider for KrumpPhysio.
- **Anyway (observability):** Traces, token usage, and tool IO are sent to Anyway via the OpenClaw plugin `@anyway-sh/anyway-openclaw` (and optionally the Python tracer around scoring). Sandbox endpoint: `https://trace-dev-collector.anyway.sh/`. Anyway does **not** process payments; it provides visibility into agent behaviour and cost.
- **Stripe (fiat payments, Anyway bounty):** For the Anyway bounty we use a dedicated **“Anyway US sandbox”** Stripe account. Payment links are created with `node canton/create-stripe-link.js` (Stripe Node SDK); metadata (`service_name=krumpbot-fit`, `tracing_id`, `environment=sandbox`) is attached for correlation in Anyway. Test product link: [KrumpPhysio Session — £5/month](https://buy.stripe.com/test_28E7sL8jg3QG1Ol5nqcZa00).

**Summary:** FLock = brain; Anyway = measure and prove; Stripe = get paid (bounty: use Anyway US sandbox account and verified setup).

---

## ClawHub skill and docs

- **Skill:** [skills/krumpphysio/SKILL.md](skills/krumpphysio/SKILL.md) — ClawHub skill so other OpenClaw agents can adopt the KrumpPhysio coaching pattern. Publish: [skills/krumpphysio/PUBLISH.md](skills/krumpphysio/PUBLISH.md).
- **Product copy:** [docs/website-description.md](docs/website-description.md)  
- **Pitch content:** [docs/PITCH-DECK-CONTENT.md](docs/PITCH-DECK-CONTENT.md)  
- **SDG 3:** [https://sdgs.un.org/goals/goal3](https://sdgs.un.org/goals/goal3)
