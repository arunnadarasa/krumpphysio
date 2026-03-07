# ZKP with Sindri — Benefits & Hackathon Value

Why we use zero-knowledge proofs (Sindri) in KrumpPhysio and what it brings to the hackathon submission.

---

## What we do with ZKP (Sindri)

- **Where:** The **Telegram video bot** runs MediaPipe locally, then forwards a short summary (joint, target angle, observed angle, smoothness) to OpenClaw so the **FLock** coach agent can reply and optionally log to Canton or create a Stripe link.
- **ZKP layer:** When `SINDRI_API_KEY` is set, we attach a **commitment** (hash) or a **full ZK proof** to that forwarded message. So the input to FLock is **verifiable**: “this summary came from a real video analysis” — without sending the video or any re-identifying data to the LLM or to third parties.

---

## Benefits for our solution

| Benefit | What it means |
|--------|----------------|
| **Verifiable input to the agent** | Judges, health authorities, or operators can be sure the coach is acting on **real** analysis, not fabricated or tampered metrics. The proof is checkable via Sindri (e.g. `proof_id`). |
| **Privacy by construction** | We prove correctness **without** exposing the video or the patient. That supports “proof without exposure” in our privacy story and helps with health-data minimisation. |
| **Trust for patients and clinics** | “Your video never leaves our server; we only send numbers, and we can prove those numbers came from a valid analysis.” That’s a clear, technical story for adoption and compliance. |
| **Stronger observability story** | Anyway gives **trace** and cost visibility; ZKP adds **cryptographic attestation** of the **input** to the agent. Together: “we see what ran” (Anyway) and “we can prove the input was legitimate” (Sindri). |
| **Differentiation** | Few hackathon projects pipe ZKP into the agent loop. We show how to add a verifiable layer to an OpenClaw + FLock pipeline without changing the core UX. |

---

## Value for the hackathon submission

### Judging and bounty fit

- **FLock track** — We use FLock as the only LLM; ZKP doesn’t replace FLock, it **augments** the **data** that goes into FLock. So we highlight: “FLock-only agent with **verifiable inputs** from the video pipeline.”
- **Anyway bounty** — Anyway = “measure and prove what happened.” ZKP = “prove the **input** to the agent was correct.” Together they support a narrative: full observability (Anyway) plus cryptographic assurance on the upstream data (Sindri).
- **Technical depth** — Shows we thought beyond “chat + tools”: we added a **privacy and verifiability** layer (ZKP + Sindri) that fits a health/physio use case.
- **SDG 3 (health)** — Trust and transparency in digital health tools support good health outcomes. ZKP helps patients and clinics trust that the AI is acting on real movement data, which supports adherence and safe use.

### One-line pitch for the deck or video

- **Short:** “We add zero-knowledge proofs (Sindri) so the coach agent’s input from video analysis is **verifiable** — without sending video or identity to the LLM.”
- **Longer:** “Video analysis runs locally; only metrics go to FLock. With Sindri we attach a ZK attestation so anyone can verify that the coach is acting on real analysis, not fake data — key for patient and health-authority trust.”

### What to show judges

1. **Demo:** Run the video bot with `SINDRI_API_KEY` set; after a video analysis, show the reply to the user and (if you forward to OpenClaw) the message body containing the ZKP note (commitment or `proof_id`). Say: “This proves the numbers came from a valid run; the video never left the server.”
2. **Docs:** Point to [SINDRI-ZKP-TELEGRAM-FLOCK.md](SINDRI-ZKP-TELEGRAM-FLOCK.md) and [PRIVACY.md](PRIVACY.md) so they see it’s implemented and documented.
3. **Slide:** One slide or one bullet: “**Verifiable inputs** — ZKP (Sindri) attests the video-bot payload to OpenClaw/FLock so the agent’s decisions are based on provable, not assumed, data.”

---

## Summary

| Question | Answer |
|----------|--------|
| What does ZKP add? | **Verifiable, minimal-disclosure input** to the FLock agent from the video pipeline. |
| Why Sindri? | Serverless proving; we don’t run circuits ourselves; fits a hackathon timeline. |
| Value for the submission? | **Trust**, **privacy**, **technical depth**, and a clear story for **Anyway** (“prove what happened”) and **FLock** (“verifiable inputs to the model”). |
