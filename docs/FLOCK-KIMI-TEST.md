# FLock Kimi real test (image + video)

Quick way to run **real LLM tests** with Kimi on the FLock API: image exercise (KrumpGotchi avatar) and video exercise (sample clip).

## Setup

1. **API key (must be from API Platform)**  
   The key must be from **[platform.flock.io](https://platform.flock.io)** (API Platform), **not** from train.flock.io or beta.flock.io.  
   At platform.flock.io: sign up → create a Team → create an API key → **Settings → Billing**: add credits (Stripe, Base Pay, or Coinbase).  
   Then in `.env`:
   ```bash
   FLOCK_API_KEY=sk-your-api-key
   ```
   If you get `401 token_not_found_in_db`, the key is from the wrong product; create a new key at platform.flock.io.

2. **Model ID**  
   Get the exact Kimi model id from the FLock marketplace (e.g. `kimi-k2.5` or `moonshot/kimi-k2.5`). Optional in `.env`:
   ```bash
   FLOCK_KIMI_MODEL=kimi-k2.5
   ```
   Default in the script is `kimi-k2.5`; change if your marketplace listing differs.

3. **Avatar**  
   The script uses `docs/krumpgotchi-assets/krumpgotchi-avatar.png`. Ensure that file exists.

## Test run: Kimi image + video (quick reference)

From repo root, with `FLOCK_API_KEY` set (e.g. in `.env`):

| Test | Command | Input |
|------|---------|--------|
| **Kimi image exercise** | `.venv-video/bin/python video/test_flock_kimi_image.py` | `docs/krumpgotchi-assets/krumpgotchi-avatar.png` |
| **Kimi video exercise** | `.venv-video/bin/python video/test_flock_kimi_video.py` | `video/samples/test_video.mp4` (or set `VIDEO_PATH`) |

Each script prints Kimi’s reply (and any reasoning). Image test works reliably; video test may report “can’t watch video” if the FLock proxy doesn’t forward video to the model yet.

## Run (image)

From repo root, with the video venv (has `httpx`):

```bash
.venv-video/bin/python video/test_flock_kimi_image.py
```

The script sends the avatar as base64 in an OpenAI-compatible `image_url` message and prints Kimi’s reply.

## Run (video)

```bash
.venv-video/bin/python video/test_flock_kimi_video.py
```

- Default video: `video/samples/test_video.mp4`. Override with `VIDEO_PATH=/path/to/clip.mp4`.
- If Kimi replies that it can't watch video or didn't receive it, the FLock proxy may not yet forward video—check the model's **API Documentation** on platform.flock.io.

## Test in Telegram (image + video with LLM reply)

From **inside Telegram**, you can get the **actual image and video** plus **Kimi’s LLM-generated** description:

1. **Setup:** Same as above: `FLOCK_API_KEY` in `.env` (or env). Start the video bot with `KRUMP_VIDEO_BOT_TOKEN` (see TEST-RUN-EXERCISES.md).

2. **In the bot chat:**
   - **`/kimi_image`** — Bot sends the KrumpGotchi avatar **image** and Kimi’s **text reply** (description) as the caption; optional reasoning in a second message.
   - **`/kimi_video`** — Bot sends the exercise **video** and Kimi’s **text reply** as the caption; optional reasoning in a second message.

So you see the real image/video in Telegram with the LLM-generated exercise commentary from Kimi.

## Real LLM-generated image in Telegram (Kimi + Replicate)

To get an **AI-generated image** (not the test avatar) in Telegram:

1. **FLock (Kimi):** `FLOCK_API_KEY` in `.env` (platform.flock.io).
2. **Replicate (image gen):** Get a token at [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) and add to `.env`:
   ```bash
   REPLICATE_API_TOKEN=r8_...
   ```
3. **In Telegram:** send **`/kimi_gen_image`**.
   - Kimi suggests a short image prompt (e.g. “KrumpGotchi doing a knee bend”).
   - Replicate (FLUX) generates the image from that prompt.
   - The bot sends the **generated image** with Kimi’s prompt as the caption.

So the image is **real LLM-generated**: idea from Kimi, image from Replicate.

**Video:** Send **`/kimi_gen_video`** in Telegram. Kimi suggests a short video prompt, then Replicate (default: `minimax/video-01`) generates a ~6s video. Takes 1–2 minutes. Same env as image (`FLOCK_API_KEY`, `REPLICATE_API_TOKEN`). Optional in `.env`: `REPLICATE_VIDEO_MODEL=minimax/video-01` (or another Replicate video model).
