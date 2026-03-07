# Sindri ZKP for Telegram → FLock (OpenClaw) Flow

Baseline knowledge from [Sindri docs](https://sindri.app/docs/introduction/) and how we use it with the KrumpPhysio Telegram video bot and FLock LLM inference.

## What is Sindri?

- **Serverless ZK proving platform** — Host circuits, generate proofs via API; supports Circom, Noir, Gnark, Halo2, Plonky2, Jolt, SP1, etc.
- **Use cases:** Verifiable computation (proof that a computation ran correctly), zkML (verifiable ML inference), attestation of data/payloads.
- **Auth:** API key in header; create/manage at [Sindri API Keys](https://sindri.app/z/me/page/settings/api-keys). Store in env (e.g. `SINDRI_API_KEY`), never in code.

## Flow in KrumpPhysio

1. **Telegram** → user sends video + caption (e.g. `/analyze left_knee 90`).
2. **Video bot** (`video/telegram_bot.py`) runs MediaPipe analysis locally, builds reply, then **forwards** a summary to OpenClaw via `forward_to_openclaw(joint, target, observed, smoothness)`.
3. **OpenClaw** receives that as synthetic user input; **FLock** (KrumpPhysio agent) reasons and can run exec (Canton log, Stripe, quantum script).

**ZKP role:** We can optionally **prove** that the payload we send to OpenClaw (joint, target, observed, smoothness) is consistent with a **committed** analysis result — e.g. attest “this OpenClaw input was derived from a valid video-bot run” without sending raw video. Sindri is used to generate that attestation proof.

## Two integration options

### Option A — Proof of payload (recommended first step)

- **Circuit:** Simple “attestation” circuit (e.g. Circom or Noir) whose **private input** is the payload `(joint, target, observed, smoothness)` and **public output** is a hash or commitment. We prove “I know a payload that hashes to this.”
- **Flow:** After `run_analysis()`, video bot calls Sindri API (Python SDK) with the payload as circuit input; gets `proof_id` and optionally verification key / calldata. Attach `proof_id` (and maybe public output) to the OpenClaw payload so the gateway or agent can verify later.
- **Benefit:** OpenClaw/FLock side can trust that the forwarded message originated from a run that produced a valid proof, without re-running MediaPipe.

### Option B — Verifiable inference (zkML)

- **Circuit:** A circuit that encodes the **LLM inference** (or a small model) so that “output = model(input)” is provable. Sindri supports zkML (e.g. [zkML on Rollkit + Celestia](https://sindri.app/blog/2024/02/21/zkml-modularity/)); full FLock-sized models are not yet practical in ZK.
- **Practical use:** For now, use Option A to prove the **input** to FLock (video-bot summary); verifiable FLock inference itself would require FLock/Sindri support for provable LLM runs (future work).

## Implementation (Option A) in this repo

- **Env:** `SINDRI_API_KEY` — if set, the video bot will attempt to generate an attestation proof before calling `forward_to_openclaw`.
- **Circuit:** We use a **pre-deployed circuit** on Sindri (e.g. a simple Circom “hash” or “multiplier” from [sindri-resources](https://github.com/Sindri-Labs/sindri-resources)) for a quick PoC; or you can upload your own attestation circuit and set `SINDRI_ATTESTATION_CIRCUIT_ID`.
- **Payload to OpenClaw:** Extended to include optional `proof_id` and `public_output` so the agent or gateway can verify via Sindri API if desired.
- **Dependency:** `sindri` (Python) in `video/requirements.txt`; install with `pip install sindri` (Python 3.10+).

## Sindri API (quick reference)

- **Create proof:** `POST /api/v1/circuit/:circuit_id/prove` with `proof_input` (JSON). Returns `proof_id`.
- **Get proof:** `GET /api/v1/proof/:proof_id` — retrieve proof, public outputs, verification key, smart contract calldata.
- **Python SDK:** `sindri.Sindri(api_key)` → `create_circuit(path)`, `prove_circuit(circuit_id, proof_input)` → `proof_id`; `get_proof(proof_id)`.

## Security

- Do not commit `SINDRI_API_KEY`. Use env vars or a secrets manager.
- Sindri recommends key rotation and expiration; use separate keys for dev/prod if possible.

## References

- [Sindri Introduction](https://sindri.app/docs/introduction/)
- [Sindri Python SDK](https://sindri.app/docs/reference/sdk/python/)
- [Getting Started — Python SDK](https://sindri.app/docs/getting-started/python-sdk/)
- [Access Management (API keys)](https://sindri.app/docs/topic-guides/access-management/)
- [Sindri-Labs/sindri-resources](https://github.com/Sindri-Labs/sindri-resources) (sample circuits + reference code)
- [zkML modularity (Sindri blog)](https://sindri.app/blog/2024/02/21/zkml-modularity/)
