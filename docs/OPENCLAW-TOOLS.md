# OpenClaw tools — parameter requirements

When using OpenClaw built-in tools from the gateway or an agent, supply **all required parameters** or you will get errors.

## Edit tool

**Error you may see:**  
`Missing required parameter: oldText (oldText or old_string). Supply correct parameters before retrying.`

**Required parameters:**

- **path** (or **file**) — Path to the file to edit.
- **old_string** or **oldText** — The **exact** string to find in the file (must match precisely, including newlines and spaces).
- **new_string** or **newText** — The replacement text.

Always pass the exact existing text as `old_string`/`oldText`; do not omit it or the tool will fail. Copy from the file (e.g. with the **read** tool) if needed, then call **edit** with that string as `old_string` and your new content as `new_string`.

**Example (conceptual):**
```json
{
  "path": "/path/to/file.md",
  "old_string": "line one\nline two",
  "new_string": "line one\nline two (updated)"
}
```

## Exec tool

For running shell commands (e.g. Canton `log-session.js`), use **exec** with **command** and optional **cwd**. No `old_string` is involved.
