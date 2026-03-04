# Krumpfit — FLock Track Project Breakdown & Timeline

**Bounty:** [AI Agents for Good – FLock Track](https://dorahacks.io/hackathon/bounty/1332) (UK AI Agent Hackathon EP4 x OpenClaw)  
**Prize pool:** $5,000 USDT (Gold $2k, Silver $1k, Bronze $800, Best Technical $600, Best Creativity $600)

---

## Key resources

| Resource | Link | Purpose |
|----------|------|--------|
| FLock API docs | https://docs.flock.io/llms-full.txt | API reference, models, auth, inference |
| Bounty brief | https://dorahacks.io/hackathon/bounty/1332 | Requirements, judging, tech stack |
| Mission Control | https://github.com/builderz-labs/mission-control | Agent dashboard, tasks, cost tracking |
| Cognee | https://github.com/topoteretes/cognee | Knowledge engine / agent memory |
| OpenClaw + FLock plugin | https://github.com/FLock-io/openclaw-plugin-flock | FLock as model provider in OpenClaw |
| RouteBox | https://github.com/createpjf/RouteBox | Optional: LLM proxy, routing, cost tracking |
| Hackathon deck | [Google Slides](https://docs.google.com/presentation/d/1ltlUH6ffmGrae3SXyIrQGa5rjAi-Bj2t0_pEIspyRs8/edit?slide=id.p1#slide=id.p1) | Context, judging criteria |

---

## Bounty requirements (must-haves)

- **Multi-channel deployment** — e.g. WhatsApp and/or Telegram  
- **FLock API only** — open-source models via FLock (no OpenAI/Anthropic for judging)  
- **OpenClaw agent framework** — core runtime  
- **SDG alignment** — real-world impact tied to UN Sustainable Development Goals  
- **Autonomous AI agents** — agentic behaviour, not just Q&A  

---

## Stage breakdown and expected timeline

### Stage 1 — Foundation & agent core  
**Goal:** Working OpenClaw agent with identity, SOUL, and FLock as sole model provider.  
**Duration:** 2–3 days  

| Task | Details | Est. time |
|------|---------|-----------|
| OpenClaw + FLock plugin | Install OpenClaw, install & enable `@openclawd/flock`, `openclaw models auth login --provider flock` | 0.5 day |
| Agent identity & SOUL | Finalise SOUL.md, IDENTITY.md, AGENTS.md; align personality with SDG (e.g. health/wellness) | 0.5 day |
| FLock model config | Pick models (e.g. `qwen3-235b`, `qwen3-30b`, `deepseek-v3.2`), set in config; test completions | 0.5 day |
| Tools & skills | Define 2–3 core tools (e.g. workout logging, habit check-in); implement and wire to agent | 1 day |
| Local E2E test | Run agent locally; verify FLock-only calls, tool use, and basic conversation | 0.5 day |

**Deliverables:** Agent runs locally, uses only FLock models, has clear identity and at least one useful tool.  
**Blockers:** FLock API key; OpenClaw ≥ 2026.1.29.

---

### Stage 2 — Multi-channel deployment  
**Goal:** Same agent reachable via WhatsApp and/or Telegram.  
**Duration:** 2–3 days  

| Task | Details | Est. time |
|------|---------|-----------|
| Channel setup | Choose WhatsApp and/or Telegram; create bot / business account; get tokens | 0.5 day |
| OpenClaw channel config | Configure channel(s) in OpenClaw; point to same agent + FLock | 1 day |
| Gateway & routing | Run OpenClaw gateway; ensure all channel traffic uses FLock (no fallback to other providers) | 0.5 day |
| Cross-channel test | Send messages on each channel; confirm replies, tools, and consistent behaviour | 1 day |
| Rate limits & safety | Basic rate limiting and guardrails so demo doesn’t break under load | 0.5 day |

**Deliverables:** At least one of WhatsApp/Telegram (or both) working with the agent; no non-FLock models in production path.  
**Blockers:** Meta/Telegram app approval if required; gateway reachable from channel webhooks.

---

### Stage 3 — SDG alignment & measurable impact  
**Goal:** Explicit SDG mapping and at least one measurable outcome (e.g. engagement, habit adherence).  
**Duration:** 1.5–2 days  

| Task | Details | Est. time |
|------|---------|-----------|
| SDG mapping | Pick 1–2 SDGs (e.g. SDG 3 Good Health), document in README or notion; tie agent goals to targets | 0.5 day |
| Metrics definition | Define 1–2 metrics (e.g. “sessions per user”, “workouts logged”, “streak days”) | 0.25 day |
| Instrumentation | Add minimal logging/counters (e.g. in tools or agent hooks) to compute metrics | 0.5 day |
| Score / dashboard | Implement `score.js` or small dashboard that reads logs and outputs metric(s) for judges | 0.5 day |

**Deliverables:** README (or Notion) section on SDG + metrics; working score script or dashboard.  
**Blockers:** None if Stage 1 tools already support the chosen metrics.

---

### Stage 4 — Memory & knowledge (optional)  
**Goal:** Persistent, searchable context (e.g. user preferences, history) to improve replies.  
**Duration:** 1–2 days  

| Task | Details | Est. time |
|------|---------|-----------|
| Cognee eval | Decide if Cognee fits (e.g. long-term user facts, workout history); read Cognee quickstart | 0.25 day |
| Integration | Add Cognee pipeline: add data (e.g. from tool outputs), cognify, optional memify; expose search to agent | 1 day |
| Agent tool | One tool that queries Cognee (e.g. “what does this user prefer?”) and injects into context | 0.5 day |

**Deliverables:** Agent can query a small knowledge graph / memory; only if time allows.  
**Blockers:** Python/Cognee env if agent stack is Node; can be a separate microservice.

---

### Stage 5 — Orchestration & monitoring (optional)  
**Goal:** Use Mission Control for tasks, cost, and visibility (optional for judging).  
**Duration:** 1–2 days  

| Task | Details | Est. time |
|------|---------|-----------|
| Mission Control setup | Clone mission-control, `pnpm install`, set `OPENCLAW_HOME`, configure gateway | 0.5 day |
| Register agent | Register Krumpfit agent; confirm heartbeat and task board visibility | 0.5 day |
| Cost tracking | Confirm token/cost data flows from gateway to Mission Control; optional budget alert | 0.25 day |

**Deliverables:** Agent visible in Mission Control; token/cost view. Optional; skip if timeline is tight.  
**Blockers:** OpenClaw gateway must be running and reachable by Mission Control.

---

### Stage 6 — Polish, demo & submission  
**Goal:** Video demo, clear README, and submission that meets all bounty criteria.  
**Duration:** 2–3 days  

| Task | Details | Est. time |
|------|---------|-----------|
| README | Project overview, SDG, how to run, env vars (no secrets), multi-channel instructions, metrics | 0.5 day |
| Demo script | 2–3 min script: problem, SDG, agent behaviour, multi-channel, FLock-only, one metric | 0.25 day |
| Video | Record demo (screen + optional voice); show WhatsApp/Telegram and at least one tool + FLock | 0.5–1 day |
| RouteBox (optional) | If used, show routing to FLock only; not required for bounty | 0.25 day |
| Submission | Submit repo + video link + short description on DoraHacks; double-check FLock + OpenClaw + multi-channel | 0.5 day |

**Deliverables:** Public repo, demo video, DoraHacks submission form filled.  
**Blockers:** None if Stages 1–3 are done.

---

## Timeline overview

| Stage | Duration | Cumulative (approx.) |
|-------|----------|------------------------|
| 1 — Foundation & agent core | 2–3 days | End of day 3 |
| 2 — Multi-channel deployment | 2–3 days | End of day 6 |
| 3 — SDG & measurable impact | 1.5–2 days | End of day 8 |
| 4 — Memory (Cognee) optional | 1–2 days | End of day 10 |
| 5 — Mission Control optional | 1–2 days | End of day 12 |
| 6 — Polish & submission | 2–3 days | End of day 15 |

**Target:** Core path (Stages 1, 2, 3, 6) in **~10–11 days**; add 4 & 5 if time allows.

---

## Dependency graph

```
Stage 1 (Foundation) ──► Stage 2 (Multi-channel) ──► Stage 3 (SDG/Metrics)
        │                           │                         │
        └───────────────────────────┴────────────────────────┘
                                    │
                                    ▼
                    Stage 4 (Cognee) ── optional, can run in parallel with 5
                    Stage 5 (Mission Control) ── optional
                                    │
                                    ▼
                    Stage 6 (Polish & submission)
```

---

## Checklist for judges (quick pass)

- [ ] Repo builds and runs with README instructions  
- [ ] Agent uses **FLock API only** (open-source models)  
- [ ] **OpenClaw** is the agent framework  
- [ ] At least **one multi-channel** (WhatsApp or Telegram) working  
- [ ] **SDG** clearly stated and tied to agent behaviour  
- [ ] At least **one measurable impact** metric implemented and shown  
- [ ] Demo video shows agent + channel + FLock in action  

---

## Notes for Notion

- Copy this file into a new Notion page (or use Notion’s Markdown import).  
- Convert the top-level sections into **toggle blocks** or **subpages** per stage if you like.  
- Use **tables** as-is; Notion will render them.  
- Add a **timeline** or **calendar** view in Notion and map the “Cumulative” column to dates from your hackathon start.  
- Keep the **Key resources** table as a quick-link block at the top.
