import os
from pathlib import Path

from anyway.sdk import Traceloop


def _load_anyway_api_key() -> str:
  """
  Resolve ANYWAY_API_KEY from the environment or from a local .env file.

  We avoid adding a python-dotenv dependency by doing a tiny parse ourselves.
  Priority:
  1. Explicit ANYWAY_API_KEY in process env
  2. ANYWAY_API_KEY=... in .env in the repo root
  """
  key = os.getenv("ANYWAY_API_KEY")
  if key:
    return key

  env_path = Path(__file__).resolve().parents[1] / ".env"
  if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
      line = line.strip()
      if not line or line.startswith("#"):
        continue
      if line.startswith("ANYWAY_API_KEY="):
        # Allow simple unquoted values; strip optional surrounding quotes
        value = line.split("=", 1)[1].strip()
        if (value.startswith('"') and value.endswith('"')) or (
          value.startswith("'") and value.endswith("'")
        ):
          value = value[1:-1]
        if value:
          return value

  raise RuntimeError(
    "ANYWAY_API_KEY is not set. "
    "Set it in your environment or add ANYWAY_API_KEY=... to your .env file."
  )


def init_anyway() -> None:
  """
  Initialise Anyway / Traceloop telemetry.

  This should be called once at process start before running a scoring session.
  """
  api_key = _load_anyway_api_key()
  app_name = os.getenv("ANYWAY_APP_NAME", "krumpphysio")

  # If tracing is explicitly disabled, no-op.
  if os.getenv("ANYWAY_DISABLED", "").lower() in {"1", "true", "yes"}:
    return

  Traceloop.init(
    app_name=app_name,
    api_endpoint="collector.anyway.sh:4317",
    headers={"Authorization": f"Bearer {api_key}"},
  )

