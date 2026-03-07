# KrumpPhysio — Privacy summary for health authorities (one page)

**Purpose:** Technical and organisational measures for data protection, for review by health authorities and data protection officers. This is not legal advice; operators remain responsible for compliance in their jurisdiction.

---

## Data protection principles (UK GDPR / EU GDPR aligned)

| Principle | How KrumpPhysio addresses it |
|-----------|------------------------------|
| **Lawfulness, fairness, transparency** | Privacy notice in the Telegram bot (`/privacy`); operator can link to a full policy. No processing of video beyond stated purpose (movement analysis). |
| **Purpose limitation** | Video used only for joint-angle analysis. Only derived metrics (joint, angles, smoothness) forwarded to the coach agent; no secondary use in the default design. |
| **Data minimisation** | No Telegram user ID or chat ID in the message body sent to the AI. Only clinical-type data (joint name, target/observed angles, smoothness). Video can be deleted immediately after analysis (configurable). |
| **Accuracy** | Analysis is automated (MediaPipe); optional zero-knowledge proof attests that the forwarded summary corresponds to a valid run without exposing raw video. |
| **Storage limitation** | Configurable retention: optional auto-delete of video after analysis; ledger (Canton) stores only scores/angles/notes with pseudonymous parties. |
| **Integrity and confidentiality** | TLS in transit; API keys and secrets via environment; no video sent to third-party clouds for analysis. Optional ZKP for verifiable integrity of the payload. |
| **Accountability** | Operator checklist (see [PRIVACY.md](PRIVACY.md)); Canton provides tamper-evident audit trail; documentation of data flows and privacy layers. |

**Special category data (health):** Where the data is considered health-related in the UK/EU, operators must ensure a valid Article 9 condition (e.g. explicit consent, or applicable national health exemption) and any required safeguards. The technical measures below support *minimisation* and *security* of such data.

---

## Key technical measures

1. **Video never leaves the analysis server** — Pose estimation runs locally (MediaPipe); no video is sent to FLock, OpenAI, or any external API. Only structured metrics are forwarded.
2. **OpenClaw → FLock message privacy layer** — Messages from the video bot to the coach are sent with explicit privacy headers (`X-KrumpPhysio-Source: video-bot`, `X-KrumpPhysio-Privacy: attested-no-pii`) so gateways and observability can treat them as minimal-PII. Message body contains no identifiers.
3. **Zero-knowledge attestation (optional)** — When enabled (Sindri), the system can prove that the coach’s input was derived from a valid analysis without revealing the underlying video or re-identifying the user.
4. **Configurable retention** — Operator can set `KRUMP_VIDEO_DELETE_AFTER_ANALYSIS=1` so each video is deleted after use; uploaded videos are excluded from version control (`.gitignore`).
5. **Pseudonymous ledger** — Canton session logs use configurable party IDs (no Telegram IDs on-ledger); no video or free-text chat stored on-ledger.
6. **Observability** — Operators can set `captureContent: false` (e.g. Anyway) so full message content is not stored, reducing exposure of any residual data in logs.

---

## Data flow (high level)

```
[Patient] → Telegram → Video bot (local analysis) → [Optional: delete video]
                ↓
         Metrics only (joint, angles, smoothness) [+ optional ZKP]
                ↓
         OpenClaw (with privacy headers) → FLock (LLM) → Reply / Canton / Stripe
```

No video or direct identifiers in the payload to OpenClaw/FLock; optional proof attests correctness without exposing data.

---

## Operator checklist (abbreviated)

- [ ] Set `KRUMP_VIDEO_DELETE_AFTER_ANALYSIS=1` or enforce short retention.
- [ ] Set `SINDRI_API_KEY` (optional ZKP) for verifiable, minimal-disclosure payloads.
- [ ] Use pseudonymous Canton parties; no Telegram IDs on-ledger.
- [ ] Configure observability with `captureContent: false` where possible.
- [ ] Publish a privacy policy and show in-bot notice (`/privacy`).
- [ ] Establish legal basis and Article 9 condition for health data (UK/EU).

---

## References

- Full document: [PRIVACY.md](PRIVACY.md)  
- ZKP (Sindri): [SINDRI-ZKP-TELEGRAM-FLOCK.md](SINDRI-ZKP-TELEGRAM-FLOCK.md)  
- UK ICO: [Guide to the UK GDPR](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/)  
- Regulation (EU) 2016/679 (GDPR), in particular Articles 5, 9, 25, 32.

---

*Last updated to include OpenClaw message privacy layer (headers for FLock) and UK/ICO–aligned wording.*
