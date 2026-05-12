#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier

python /app/demo.py

python - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("runs/latest/results.json").read_text(encoding="utf-8"))
scores = {row["name"]: row["correct"] for row in payload["leaderboard"]}
expected = {
    "no_memory": 1,
    "keyword_memory": 2,
    "update_aware_memory": 3,
}

if scores != expected:
    raise SystemExit(f"unexpected leaderboard: {scores}")
PY

echo 1 > /logs/verifier/reward.txt
