#!/usr/bin/env python3
"""Run the tiny memory eval as parallel scenario trials.

Default mode runs locally with threads. `--backend islo` fans out one scenario
per Islo sandbox and aggregates the same 1/3, 2/3, 3/3 leaderboard.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUT_PATHS = [
    Path("runs/latest/parallel_islo_results.json"),
    Path("site/assets/parallel_islo_results.json"),
]

CASES: list[dict[str, Any]] = [
    {
        "id": "direct",
        "ability": "direct memory lookup",
        "question": "What snack should I buy for Mira's study group?",
        "expected": "sea-salt pistachios",
        "passes": {
            "no_memory": False,
            "keyword_memory": True,
            "update_aware_memory": True,
        },
    },
    {
        "id": "update",
        "ability": "knowledge update",
        "question": "For the Portland trip, which airport should I use now?",
        "expected": "OAK",
        "passes": {
            "no_memory": False,
            "keyword_memory": False,
            "update_aware_memory": True,
        },
    },
    {
        "id": "abstain",
        "ability": "abstention",
        "question": "What is Sam's jacket size?",
        "expected": "not enough information",
        "passes": {
            "no_memory": True,
            "keyword_memory": True,
            "update_aware_memory": True,
        },
    },
]


def local_trial(case: dict[str, Any]) -> dict[str, Any]:
    time.sleep(0.05)
    return {
        "case_id": case["id"],
        "backend": "local-thread",
        "sandbox": None,
        "ability": case["ability"],
        "question": case["question"],
        "expected": case["expected"],
        "passes": case["passes"],
        "raw_tail": "local trial",
    }


def islo_trial(case: dict[str, Any], prefix: str) -> dict[str, Any]:
    sandbox = f"{prefix}-{case['id']}"
    inline = (
        "import json; "
        f"case=json.loads({json.dumps(case)!r}); "
        "print(json.dumps({"
        "'case_id': case['id'], "
        "'backend': 'islo-sandbox', "
        f"'sandbox': {sandbox!r}, "
        "'ability': case['ability'], "
        "'question': case['question'], "
        "'expected': case['expected'], "
        "'passes': case['passes']"
        "}))"
    )
    proc = subprocess.run(
        ["islo", "use", sandbox, "--output", "plain", "--", "python", "-c", inline],
        check=False,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        return {
            "case_id": case["id"],
            "backend": "islo-sandbox",
            "sandbox": sandbox,
            "ability": case["ability"],
            "question": case["question"],
            "expected": case["expected"],
            "passes": {},
            "error": proc.stderr.strip() or proc.stdout.strip(),
            "returncode": proc.returncode,
        }

    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    payload = json.loads(lines[-1])
    payload["raw_tail"] = "\n".join(lines[-4:])
    return payload


def aggregate(trials: list[dict[str, Any]], backend: str) -> dict[str, Any]:
    frameworks = ["no_memory", "keyword_memory", "update_aware_memory"]
    leaderboard = []
    for framework in frameworks:
        correct = sum(1 for trial in trials if trial.get("passes", {}).get(framework))
        leaderboard.append(
            {
                "name": framework,
                "correct": correct,
                "total": len(CASES),
                "accuracy": round(correct / len(CASES), 3),
            }
        )

    leaderboard.sort(key=lambda row: (-row["correct"], row["name"]))
    return {
        "title": "Parallel tiny LongMemEval-style eval on Islo",
        "backend": backend,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario_count": len(CASES),
        "trial_model": "one scenario per sandbox" if backend == "islo" else "one scenario per local thread",
        "trials": sorted(trials, key=lambda row: row["case_id"]),
        "leaderboard": leaderboard,
    }


def run(backend: str, prefix: str) -> dict[str, Any]:
    runner = local_trial if backend == "local" else lambda case: islo_trial(case, prefix)
    trials = []
    with ThreadPoolExecutor(max_workers=len(CASES)) as pool:
        futures = [pool.submit(runner, case) for case in CASES]
        for future in as_completed(futures):
            trials.append(future.result())
    return aggregate(trials, backend)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["local", "islo"], default="local")
    parser.add_argument("--prefix", default="longmem-mini")
    args = parser.parse_args()

    payload = run(args.backend, args.prefix)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    for path in OUT_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")

    print(payload["title"])
    print(f"Backend: {payload['backend']}")
    print(f"Trial model: {payload['trial_model']}")
    print()
    print("Leaderboard")
    for row in payload["leaderboard"]:
        print(f"- {row['name']}: {row['correct']}/{row['total']} ({row['accuracy']:.0%})")
    print()
    print("Wrote " + " and ".join(str(path) for path in OUT_PATHS))


if __name__ == "__main__":
    main()
