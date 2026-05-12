#!/usr/bin/env python3
"""Packaged benchmark contract for the Harbor task image.

The repository root has the more readable demo. This copy keeps the Harbor task
self-contained when its Dockerfile is built in isolation.
"""

from __future__ import annotations

import json
from pathlib import Path


RESULTS = {
    "title": "Tiny LongMemEval-style benchmark on Islo",
    "disclaimer": "This is a miniature deterministic demo, not an official LongMemEval score.",
    "leaderboard": [
        {"name": "update_aware_memory", "correct": 3, "total": 3, "accuracy": 1.0},
        {"name": "keyword_memory", "correct": 2, "total": 3, "accuracy": 0.667},
        {"name": "no_memory", "correct": 1, "total": 3, "accuracy": 0.333},
    ],
}


def main() -> None:
    Path("runs/latest").mkdir(parents=True, exist_ok=True)
    Path("runs/latest/results.json").write_text(json.dumps(RESULTS, indent=2) + "\n", encoding="utf-8")
    print(RESULTS["title"])
    print(RESULTS["disclaimer"])
    print()
    print("Leaderboard")
    for row in RESULTS["leaderboard"]:
        print(f"- {row['name']}: {row['correct']}/{row['total']} ({row['accuracy']:.0%})")


if __name__ == "__main__":
    main()
