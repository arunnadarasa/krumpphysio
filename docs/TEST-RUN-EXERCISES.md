# Test run: Image + video exercises with KrumpGotchi

How to do a quick test of **image exercises** and **video exercises** for KrumpGotchi (and optionally try them in Telegram or the Lovable app).

---

## 1. Quick test in the browser (no server)

**Steps:**

1. **Image:** Already set. The default avatar is at `docs/krumpgotchi-assets/krumpgotchi-avatar.png` and is used in the demo page.

2. **Video (optional):** Add one short exercise clip (e.g. 5–15 s MP4) so the video block works:
   - Save it as `docs/krumpgotchi-assets/exercises/sample.mp4`.
   - Or use any short MP4 and name it `sample.mp4` in that folder.

3. **Open the demo page:**
   - Open `docs/krumpgotchi-assets/exercise-demo.html` in a browser (double‑click or File → Open).
   - You should see:
     - **Image exercise** — KrumpGotchi default avatar.
     - **Video exercise** — Video player; if you added `sample.mp4`, it will play.

That’s the minimal “test run” for image + video exercises with KrumpGotchi.

---

## 2. Optional: serve the page locally (same-origin)

If the video doesn’t load when opening the file directly (some browsers restrict `file://` for video), serve the folder:

```bash
cd /Users/openclaw/Documents/KrumpPhysio/docs/krumpgotchi-assets
python3 -m http.server 8888
```

Then open **http://localhost:8888/exercise-demo.html** in the browser. Image and video will load from the same origin.

---

## 3. Optional: use assets in the Lovable KrumpGotchi app

- Upload `krumpgotchi-avatar.png` and (if you have it) `exercises/sample.mp4` (or your exercise clips) into the Lovable project’s assets (e.g. `public/` or `src/assets/`).
- Add a section like “Try an exercise” that shows:
  - One **image** (e.g. default avatar or a left-knee exercise image).
  - One **video** (e.g. `<video src="/sample.mp4" controls />`).
- That gives you the same “image + video exercise” test run inside the real app.

---

## 4. Telegram: see KrumpGotchi image + video in the bot

To test “exercise in Telegram” (bot sends one image and one video):

1. **Assets:** Reuse the same files (avatar image + `sample.mp4` or another short clip). The bot needs to read them from disk (e.g. repo path) or from URLs.

2. **Bot command:** Add a handler (e.g. `/exercise_demo`) that:
   - Sends a **photo** (e.g. `krumpgotchi-avatar.png` or an exercise image) with caption “KrumpGotchi — Image exercise (e.g. left knee focus)”.
   - Sends a **video** (e.g. `exercises/sample.mp4`) with caption “Video exercise demo”.
   - Use `context.bot.send_photo(chat_id, photo=open(path, "rb"), caption="...")` and `context.bot.send_video(chat_id, video=open(path, "rb"), caption="...")`.

3. **Run the bot**, then in Telegram send `/exercise_demo` and confirm you get the image and the video.

**Quick steps:** From repo root, set `KRUMP_VIDEO_BOT_TOKEN` (from BotFather), run `.venv-video/bin/python video/telegram_bot.py`, then in Telegram send `/exercise_demo`. The bot sends the avatar image and a sample video (from `video/samples/test_video.mp4` if `exercises/sample.mp4` is missing).

That’s the full test run for image exercises and video exercises with KrumpGotchi (browser first, then Lovable and Telegram if you want).
