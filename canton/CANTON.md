# Canton / Daml local setup (KrumpPhysio)

## `sandbox-classic` is not available

In current Daml SDKs there is no `daml sandbox-classic` command. Use one of these instead:

- **Option A – All-in-one:** From the Daml project run:
  ```bash
  cd /Users/openclaw/canton/krumpphysio-daml
  daml start
  ```
  This starts the Sandbox, Navigator, and HTTP JSON API (default port 7575). The ledger ID is often **`sandbox`** when using this flow.

- **Option B – Canton sandbox + JSON API:** Run the Canton sandbox and JSON API separately. When the sandbox starts, **note the ledger ID** in the console (it may be `sandbox` or e.g. `sandbox-<uuid>`). Start the JSON API pointing at that sandbox.

## JWT for local development

The JSON API expects a Bearer JWT with a **ledgerId** claim. For a ledger without strict auth you can use a dev token.

1. Set (or export) before generating the token:
   - `CANTON_LEDGER_ID` – same as the ledger ID from your sandbox (default: `sandbox`)
   - `CANTON_PHYSIO_PARTY` – party that will submit commands (e.g. the physio party ID from your ledger)

2. Generate a JWT (from the KrumpPhysio repo):
   ```bash
   cd /Users/openclaw/Documents/KrumpPhysio
   node canton/jwt-dev.js
   ```

3. Put the printed token in your `.env` as:
   ```bash
   CANTON_JWT=<paste token here>
   ```

4. Also set in `.env`:
   - `CANTON_ENABLE=true`
   - `CANTON_JSON_API_BASE_URL=http://localhost:7575` (if the JSON API is on another host/port, change this)
   - `CANTON_PATIENT_PARTY` and `CANTON_PHYSIO_PARTY` to the allocated party IDs from your ledger

If you see **401 "ledgerId missing in access token"**, the JWT payload is wrong or the ledger ID does not match: fix `CANTON_LEDGER_ID` (and, if needed, the party IDs), then run `node canton/jwt-dev.js` again and update `CANTON_JWT`.

## Allocating parties (correct syntax)

The party name is a **positional** argument, not `--party`. With `daml start` running (sandbox on 6865):

```bash
cd /Users/openclaw/canton/krumpphysio-daml

daml ledger allocate-party --host localhost --port 6865 KrumpPhysioPatient
daml ledger allocate-party --host localhost --port 6865 KrumpPhysioClinic
```

Then list parties and copy the full `identifier` values for your `.env`:

```bash
curl -s -X GET \
  -H "Authorization: Bearer YOUR_JWT" \
  http://localhost:7575/v1/parties
```

Use the `identifier` strings (e.g. `sandbox::1220...`) as `CANTON_PATIENT_PARTY` and `CANTON_PHYSIO_PARTY`.

**Template ID:** The JSON API expects `<packageId>:<module>:<entity>` (two colons). The default in code uses the krumpphysio-ledger package hash. If you rebuild the DAR, copy the template ID from Navigator (e.g. `KrumpPhysio.Rehab:SessionLog@<hash>`) and set `CANTON_SESSIONLOG_TEMPLATE_ID=<hash>:KrumpPhysio.Rehab:SessionLog`.

## Agent / Telegram: log when the agent decides

To have the agent (e.g. on Telegram) log sessions to Canton when it gives a score, see [canton/OPENCLAW-TOOL.md](OPENCLAW-TOOL.md): register the `log_krumpphysio_session` tool and ensure the agent’s IDENTITY instructs it to call the tool after scoring.
