# Lovable prompt: KrumpGotchi website (link Telegram + gamification)

Copy the text below into Lovable to generate the web app that links with the KrumpPhysio Telegram bot and future KrumpGotchi features.

---

## Prompt to paste into Lovable

```
Build a single-page or few-page web app called **KrumpGotchi** that links with the KrumpPhysio Telegram bot and gamifies rehab.

**Core features**

1. **Link Telegram**
   - A "Link Telegram" button or section.
   - When the user clicks it, show instructions: "Message the KrumpPhysio bot on Telegram with the command /link. You will receive a 6-character code. Enter it below within 5 minutes."
   - An input field for the code and a "Verify" button.
   - On submit, call the backend API: GET `{LINK_API_URL}/api/link/verify?code=XXXXXX` (replace LINK_API_URL with an env variable, e.g. https://your-link-api.ngrok.io or your deployed API URL). If the response is 200, the body is `{ "telegram_id": 123, "telegram_username": "joe" }`. Store this (e.g. in local state, or in your auth/database) as the linked Telegram account for the current user. Show success: "Telegram linked! Your KrumpGotchi will sync with this account."
   - If 404 or error, show "Invalid or expired code. Get a new code with /link in Telegram."

2. **My KrumpGotchi**
   - A section or page that shows the user's **KrumpGotchi** (their rehab companion). For now it can be a simple avatar or mascot image with a name (e.g. "Your KrumpGotchi") and placeholder text: "Points: 0" and "No items equipped yet." Later this will show points earned from doing KrumpPhysio exercises and items purchased with those points.

3. **Points and shop (placeholder)**
   - Display "Points: 0" prominently. Explain in one line: "Earn points by doing KrumpPhysio on Telegram (video analysis, sessions)."
   - A "Shop" or "Items" section with 2–3 placeholder rare items (e.g. "Rare Headband — 500 pts", "Battle Wristband — 200 pts", "Gold Stomp Badge — 1000 pts"). Buttons can be disabled with "Coming soon" or "Link Telegram to earn points."

4. **Community / social proof (placeholder)**
   - A short section: "Other KrumpGotchis" or "Leaderboard" with 2–3 placeholder avatar cards (e.g. "BattleName1 — 120 pts", "BattleName2 — 80 pts") to show the future social/leaderboard feature. No real data required; just UI.

**Design and copy**
- Fun, gamified, and consistent with **Krump** / street dance / battle culture. Use bold typography, high contrast, and a dark or vibrant colour scheme (e.g. dark background with neon or strong accent colours).
- Tagline: "Your rehab companion. Link Telegram, earn points, unlock rare gear."
- Footer: "Powered by KrumpPhysio. Rehab as battle rounds."

**Tech**
- Use a simple auth or session so "current user" can hold a linked Telegram ID (e.g. after verify, save to localStorage or your backend). You can use anonymous auth or email-only sign-up for the web account; linking Telegram is the key action.
- LINK_API_URL must be configurable (env or app config) so the frontend calls the correct backend (the KrumpPhysio link API that verifies codes from the Telegram bot).
- Mobile-friendly layout so patients can open the site on their phone, get the code from Telegram, and enter it in the same session.
```

---

## After you create the app in Lovable

1. **Set the API URL**  
   In your Lovable app config (or env), set `LINK_API_URL` to the base URL of your link API:
   - **Local:** Run `python video/link_api.py` and expose it with ngrok: `ngrok http 8765` → use the ngrok URL (e.g. `https://abc123.ngrok.io`) as `LINK_API_URL`.
   - **Deployed:** Deploy `video/link_api.py` (e.g. Railway, Render, Fly.io) and set `LINK_API_URL` to that base URL.

2. **Set the website URL in the bot**  
   In your `.env` (for the Telegram bot), set:
   ```bash
   LINK_WEBSITE_URL=https://your-app.lovable.app
   ```
   (or whatever your Lovable app URL is). Then when users send `/link` to the bot, they see this URL in the reply.

3. **Run the link API and expose it**  
   The Lovable app runs in the browser at `krumpgotchi.lovable.app`, so it can only call URLs that are **publicly reachable**. Localhost won’t work.
   - **Option A (local dev):** Run the API and expose it with ngrok:
     ```bash
     cd /path/to/KrumpPhysio
     .venv-video/bin/python video/link_api.py
     # In another terminal:
     ngrok http 8765
     ```
     Use the ngrok URL (e.g. `https://abc123.ngrok-free.app`) as `LINK_API_URL` in Lovable.
   - **Option B:** Deploy the link API (e.g. Railway, Render, Fly.io) and set `LINK_API_URL` in Lovable to that base URL.
   - Default port is 8765; override with `LINK_API_PORT` if needed. The Telegram bot and the link API must share the same `data/` directory (same repo deploy) so codes created by the bot are visible to the API.
   - **CORS:** The API allows `https://krumpgotchi.lovable.app` by default. If your app URL is different, set `LINK_CORS_ORIGINS` (comma-separated) when running the API.

---

## API reference (for the website)

- **GET** `{LINK_API_URL}/api/link/verify?code=XXXXXX`  
  - Success (200): `{ "telegram_id": 123456789, "telegram_username": "joe" }`  
  - Invalid/expired (404): `{ "error": "Invalid or expired code" }`  
  - The code is one-time: after a successful verify, it is consumed and cannot be used again.

- **GET** `{LINK_API_URL}/api/link/health`  
  - Returns `{ "status": "ok" }` for liveness checks.

---

## Troubleshooting: "Could not reach the server"

- **Cause:** The browser (on krumpgotchi.lovable.app) cannot reach your link API — usually because the API URL is wrong or the API is not publicly reachable.
- **Fix:**
  1. Run the link API: `python video/link_api.py` (and keep it running).
  2. Expose it: use **ngrok** (`ngrok http 8765`) or deploy the API to a public host.
  3. In Lovable (project env / config), set **LINK_API_URL** to that public base URL (e.g. `https://your-ngrok-url.ngrok-free.app`). No trailing slash.
  4. Retry "Verify" on the Link Telegram page. The API now sends CORS headers so requests from `https://krumpgotchi.lovable.app` are allowed.

---

## Setting the API URL in the Lovable project

In the generated Lovable app, the link API base URL is in **`src/config.ts`** (around line 8):

```ts
export const LINK_API_URL = "https://your-actual-ngrok-url.ngrok.io";
```

Replace the placeholder with your real API URL (from ngrok or your deployed link API). No trailing slash. After saving, the "Verify" button on the Link Telegram page will call your API and linking will work.

---

## Optional enhancements (prompts for Lovable)

Use these in Lovable if you want to refine the app:

**1. Set up the API connection**  
Already done once you set `LINK_API_URL` in `src/config.ts` to your ngrok or deployed URL. Optionally: "Use an environment variable for LINK_API_URL so we can change it per environment without editing code."

**2. Add navigation bar**  
"Add a simple top navigation bar to KrumpGotchi with links: Home (or My KrumpGotchi), Link Telegram, Shop, and Leaderboard / Community. Match the dark theme and Krump vibe. Mobile-friendly (hamburger on small screens)."

**3. Enhance animations**  
"Add subtle animations to the KrumpGotchi app: gentle pulse or glow on the main CTA (Verify / Link Telegram), light motion on the KrumpGotchi avatar or mascot, and smooth transitions when switching sections. Keep it snappy and on-brand (battle / street dance energy), not distracting."
