# OpenClaw web_search — Kimi (configured) and alternatives

The **web_search** tool is configured to use **Kimi** (Moonshot) as the provider. FLock already provides Kimi models; web_search uses the Kimi/Moonshot API for search.

## Kimi (configured)

Config in `~/.openclaw/openclaw.json`:

```json
"tools": {
  "web": {
    "search": {
      "provider": "kimi",
      "kimi": {}
    }
  }
}
```

Set your key **in the environment** where the gateway runs:

```bash
export KIMI_API_KEY=your-kimi-key-here
# or
export MOONSHOT_API_KEY=your-moonshot-key-here
openclaw gateway
```

Or add to `~/.openclaw/.env` (if OpenClaw loads it):  
`KIMI_API_KEY=...` or `MOONSHOT_API_KEY=...`

Get a key from [Moonshot / Kimi](https://platform.moonshot.cn/) (or your FLock/Kimi provider). Restart the gateway after setting the key.

## Optional: API key in config

Instead of the env var, put the key in config:

```json
"kimi": {
  "apiKey": "your-kimi-key-here"
}
```

## Other providers (Brave, Perplexity, Gemini, Grok)

Allowed in OpenClaw 2026.3.x: `brave`, `perplexity`, `grok`, `gemini`, `kimi`. See [OpenClaw Web tools](https://docs.openclaw.ai/tools/web).

## If you don’t use web search

Add to the agent’s instructions: “Do not use the web_search tool” (or only when the user explicitly asks for a web search).
