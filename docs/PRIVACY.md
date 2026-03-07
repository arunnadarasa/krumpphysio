# KrumpPhysio — Privacy & Data Protection

This document describes the **privacy layers** built into KrumpPhysio so **patients** and **health authorities** can trust the solution. It is intended for deployment teams, compliance review, and for sharing with clinicians and regulators.

**One-page summary for health authorities (UK/ICO and GDPR-oriented):** [PRIVACY-HEALTH-AUTHORITY-SUMMARY.md](PRIVACY-HEALTH-AUTHORITY-SUMMARY.md).

---

## 1. Principles

- **Data minimization** — We only process what is needed to score movement and support rehab.
- **No unnecessary retention** — Video and identifiers can be discarded or pseudonymised as soon as analysis is done (configurable).
- **Verifiable without exposing** — Zero-knowledge attestation (ZKP) allows proving that analysis was done correctly without sending raw video or re-identifiable data to third parties.
- **Transparency** — Users see what happens to their data; operators can show health authorities a clear data flow and retention policy.
- **Auditability** — Where used, the Canton ledger provides a tamper-evident record of sessions (scores, angles, notes) without requiring raw video or Telegram IDs on-ledger.

---

## 2. What We Process (by component)

### 2.1 Telegram video bot (video sidecar)

| Data | Where it lives | Retention | Purpose |
|------|----------------|-----------|---------|
| Incoming video file | Locally on server (path: `video/telegram/<chat_id>_<message_id>.mp4`) | **Configurable:** delete immediately after analysis (see §4) or keep for debugging. Default: keep until operator deletes. | Pose analysis (MediaPipe) only; no cloud video upload. |
| Analysis result | In memory → reply to user; optionally forwarded to OpenClaw | Not stored by the bot beyond the reply. | Score, smoothness, joint angles. |
| Forwarded payload to OpenClaw | Text body: joint name, target angle, observed angle, smoothness. **No Telegram user ID or chat ID in the payload body.** | Depends on OpenClaw/gateway and observability (Anyway) config. | So the coach agent can respond and optionally log to Canton / Stripe. |
| Optional ZKP | Commitment hash or proof_id (+ public output) attached to the same message. | Same as payload. | Prove “this summary came from a valid analysis” without sending video. |

**Important:** The video bot does **not** send the video itself to FLock, OpenClaw, or any external API. Only structured metrics (and optional ZKP) are forwarded. Video stays on the machine running the bot (or is deleted after analysis if enabled).

### 2.2 OpenClaw + FLock (coach agent)

- **Input:** Free-text chat and/or the forwarded message from the video bot (joint, target, observed, smoothness, optional ZKP).
- **Processing:** FLock LLM runs on OpenClaw; no video is ever sent to the LLM.
- **Output:** Replies, and optionally exec (Canton log, Stripe link, quantum script). Observability (e.g. Anyway) may log prompts/responses if enabled; operators can set `captureContent: false` to avoid storing full message content (see [skills/krumpphysio/SKILL.md](../skills/krumpphysio/SKILL.md)).

### 2.3 Canton (session ledger)

- **On-ledger:** Session contracts (e.g. `SessionLog`) contain: score, round, angles (e.g. joint/target/observed), notes. Parties are **configurable** (e.g. `CANTON_PATIENT_PARTY`, `CANTON_PHYSIO_PARTY`) and typically are **pseudonymous** (e.g. role-based or clinic-assigned IDs), not raw Telegram IDs.
- **No video, no chat text, no PII** is written to the ledger by the default scripts.

### 2.4 Stripe / payments

- Payment links are created by the agent via `create-stripe-link.js`; metadata can include service name and tracing ID. Card and payer data are handled by Stripe according to Stripe’s privacy policy and PCI obligations, not by KrumpPhysio application code.

---

## 3. Privacy-by-design features

### 3.1 Zero-knowledge attestation (ZKP — Sindri)

- When **Sindri** is configured (`SINDRI_API_KEY`), the video bot can attach a **commitment** (hash) or a **ZK proof** to the payload sent to OpenClaw.
- **Effect:** A health authority or auditor can be assured that the coach agent is acting on the basis of a **real** analysis (provable without revealing the underlying video or re-identifying the user from the proof).
- See [SINDRI-ZKP-TELEGRAM-FLOCK.md](SINDRI-ZKP-TELEGRAM-FLOCK.md).

### 3.2 Local-first video analysis

- Pose estimation (MediaPipe) runs **on the server** that hosts the video bot. Video is **not** sent to OpenAI, FLock, or any third party for analysis.
- Only the **result** (angles, smoothness) is sent onward, optionally with a ZK attestation.

### 3.3 Minimal payload to the coach

- The text we forward to OpenClaw contains **no** Telegram user ID, chat ID, or name in the body. Only: joint, target angle, observed angle, smoothness (and optional ZKP). Routing/identifiers are handled by the channel (e.g. Telegram plugin) separately if needed.

### 3.4 Configurable retention and deletion

- **Video files:** Operator can enable **automatic deletion** of each video file immediately after successful analysis (`KRUMP_VIDEO_DELETE_AFTER_ANALYSIS=1`). See §4.
- **Logs:** Debug logs (e.g. `.cursor/debug-*.log`) are optional and can be disabled or excluded from production; they may contain joint/target and reply preview but not full video or Telegram IDs if the codebase is used as intended.

### 3.5 Canton: pseudonymous parties

- Ledger contracts use configurable party IDs. Operators can map “patient” to a clinic-assigned ID or role, so the ledger does not need to store Telegram or other direct identifiers.

### 3.6 OpenClaw message privacy layer (for FLock)

- Every message the **video bot** sends to the OpenClaw gateway (and thus to FLock) includes **privacy headers** so the stack can treat the message as minimal-PII:
  - **`X-KrumpPhysio-Source: video-bot`** — Identifies the message as coming from the video sidecar (not free-text chat). Gateways or middleware can apply different retention or logging rules (e.g. do not log message body).
  - **`X-KrumpPhysio-Privacy: attested-no-pii`** — Signals that the message body contains no direct identifiers (no Telegram user/chat ID, no names) and may be ZKP-attested when Sindri is enabled.
- **Effect:** OpenClaw and any proxy or observability layer (e.g. Anyway) can honour these headers to avoid storing or forwarding full message content where policy requires it. Combined with `captureContent: false`, this adds a **privacy layer around the OpenClaw message** itself when used with FLock.
- The message **body** remains minimal (joint, angles, smoothness, optional ZKP note); no code path adds Telegram IDs or PII into the `input` text.

---

## 4. Operator checklist (for health authority confidence)

Deployers can use this to demonstrate due care:

- [ ] **Video retention:** Set `KRUMP_VIDEO_DELETE_AFTER_ANALYSIS=1` so video is deleted after analysis, or define and enforce a short retention window.
- [ ] **ZKP:** Set `SINDRI_API_KEY` (and optionally `SINDRI_ATTESTATION_CIRCUIT_ID`) so forwarded payloads are verifiable without exposing raw data.
- [ ] **Observability:** If using Anyway, consider `captureContent: false` so full message content is not stored; keep tool IO if needed for debugging. Messages from the video bot are sent with `X-KrumpPhysio-Privacy: attested-no-pii` so middleware can treat them as minimal-PII.
- [ ] **Canton parties:** Use pseudonymous or role-based party IDs; do not put Telegram IDs or other direct identifiers in ledger payloads unless required and legally justified.
- [ ] **.env and secrets:** Never commit API keys or tokens; use env vars or a secrets manager. Ensure `video/telegram/` (uploaded videos) is not committed (e.g. in `.gitignore`).
- [ ] **Privacy notice:** Show users a short notice (e.g. in the bot with `/privacy` or on first use) and link to a full policy if you publish one. See §5.

---

## 5. User-facing privacy notice (suggested)

Operators can show something like this in the Telegram bot (e.g. `/privacy` or in the welcome message):

- **What we use:** Your video is used only to analyse the joint angle you asked for. Analysis runs on our server; we do not send your video to other companies.
- **What we keep:** We only keep the numbers (joint, target angle, observed angle, smoothness) so your coach can give you feedback and, if you choose, log the session. We can delete your video right after analysis if our operator enables that.
- **Proof without exposing:** When we use optional privacy tech (zero-knowledge proofs), we can prove the analysis was done correctly without sharing your video or identity.
- **Your rights:** Ask the operator for access, correction, or deletion of your data. For payments, Stripe’s privacy policy applies.

Adjust wording to match your jurisdiction (e.g. GDPR, UK DPA, local health data rules) and your actual retention and processing.

---

## 6. Compliance and jurisdiction (UK GDPR / EU GDPR)

- This document is a **technical and organisational** description of the privacy layers in the KrumpPhysio codebase. It is not legal advice.
- **UK ICO / EU GDPR:** The measures described support compliance with data protection principles (lawfulness, purpose limitation, data minimisation, storage limitation, integrity and confidentiality, accountability). For a one-page alignment with UK GDPR and health data, see [PRIVACY-HEALTH-AUTHORITY-SUMMARY.md](PRIVACY-HEALTH-AUTHORITY-SUMMARY.md).
- **Special category data (health):** Where processing involves health-related data in the UK or EU, operators must ensure a valid condition under Article 9 UK GDPR / GDPR (e.g. explicit consent, or a permitted exemption under national law) and implement appropriate safeguards. The technical measures above (minimisation, no identifiers in OpenClaw body, optional ZKP, retention controls) support such safeguards.
- Operators are responsible for:
  - Determining the legal basis for processing (e.g. consent, legitimate interest, health exemption).
  - Applying sector rules (e.g. health data, medical devices) in their jurisdiction.
  - Providing their own privacy policy and, where required, data processing agreements with sub-processors (e.g. FLock, Stripe, Sindri, Anyway).

---

## 7. Summary table (for quick reference)

| Concern | Mitigation |
|--------|------------|
| Video leaving the system | Video stays on bot server; only metrics (+ optional ZKP) sent to OpenClaw. Optional auto-delete after analysis. |
| Re-identification from forwarded data | Payload to OpenClaw has no Telegram ID in body; Canton uses configurable pseudonymous parties. |
| Proving analysis without exposing data | Optional Sindri ZKP: commitment or proof attached to payload. |
| Long-term video retention | Configurable: delete after analysis or enforce retention policy. |
| Audit trail | Canton ledger (scores, angles, notes) without raw video or PII. |
| Transparency | Privacy notice in bot; this doc and one-pager for authorities and deployers. |
| OpenClaw/FLock message | Privacy headers (`X-KrumpPhysio-Source`, `X-KrumpPhysio-Privacy`); minimal body; observability can avoid storing content. |

---

*Last updated to reflect OpenClaw message privacy layer (headers for FLock), UK/ICO and GDPR wording, and [PRIVACY-HEALTH-AUTHORITY-SUMMARY.md](PRIVACY-HEALTH-AUTHORITY-SUMMARY.md).*
