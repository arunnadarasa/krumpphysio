#!/usr/bin/env python3
"""
Run a KrumpPhysio scoring session with Anyway telemetry.

Usage:
  python -m telemetry.trace_score '<angles_json>' <round>

Example:
  python -m telemetry.trace_score '[{"joint":"left_shoulder","target":120,"observed":118}]' 1
"""

import json
import subprocess
import sys
from pathlib import Path

from anyway.sdk.decorators import workflow, task

from .anyway_tracer import init_anyway


@task(name="call_krumpphysio_score")
def call_krumpphysio_score(angles_json: str, round_label: str) -> str:
  """
  Task: delegate to the existing Node-based scoring pipeline.

  This keeps OpenClaw + FLock as-is while giving Anyway a task span for the
  external scoring work.
  """
  repo_root = Path(__file__).resolve().parents[1]
  cmd = ["node", "score.js", angles_json, round_label]

  proc = subprocess.run(
    cmd,
    cwd=str(repo_root),
    capture_output=True,
    text=True,
  )

  if proc.returncode != 0:
    # Surface stderr to the caller; Anyway will mark this span/trace as error.
    raise RuntimeError(proc.stderr.strip() or f"score.js exited with {proc.returncode}")

  return proc.stdout


@workflow(name="krumpphysio_scoring_session")
def scoring_session(angles_json: str, round_label: str) -> str:
  """
  Workflow: one KrumpPhysio scoring session.

  We also parse angles_json so Anyway can surface richer attributes in traces.
  """
  try:
    angles = json.loads(angles_json)
  except json.JSONDecodeError:
    angles = None

  # NOTE: The decorators take care of span creation; we just call the task.
  return call_krumpphysio_score(angles_json, round_label)


def main() -> None:
  if len(sys.argv) != 3:
    print("Usage: python -m telemetry.trace_score '<angles_json>' <round>")
    sys.exit(1)

  angles_json = sys.argv[1]
  round_label = sys.argv[2]

  # Ensure Anyway telemetry is initialised before we run the workflow.
  init_anyway()

  text = scoring_session(angles_json, round_label)
  sys.stdout.write(text)


if __name__ == "__main__":
  main()

