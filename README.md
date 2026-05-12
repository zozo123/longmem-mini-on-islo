# Tiny Long-Memory Benchmark on Islo

A 60-second demo of long-term memory evaluation, built for an Islo sandbox and wrapped as a tiny Harbor task.

This is **not** an official LongMemEval score. It is a small, inspectable demo that shows why long-memory systems need to handle retrieval, updates, and abstention.

Project page:

```text
https://zozo123.github.io/longmem-mini-on-islo/
```

## What This Demo Benchmarks

The benchmark uses one short multi-session chat history and 3 questions:

1. Direct memory lookup: recover a stored preference.
2. Knowledge update: prefer the newest fact over a stale fact.
3. Abstention: say there is not enough information when memory does not contain the answer.

It compares 3 simple memory approaches:

| Approach | What it does | Expected result |
| --- | --- | --- |
| `no_memory` | Has no persisted chat history and abstains. | `1/3` |
| `keyword_memory` | Retrieves the best keyword-overlap session. | `2/3` |
| `update_aware_memory` | Retrieves relevant sessions, prefers newer facts for update questions, and abstains when evidence is missing. | `3/3` |

The goal is not to win a benchmark. The goal is to make the failure modes obvious enough to explain in one Hacker News page.

## Parallel Sandbox Eval

The better Islo demo is the parallel version: one simple scenario per sandbox, all launched from a local script.

```bash
python3 parallel_islo_eval.py --backend islo --prefix longmem-mini
```

This fans out 3 scenario trials:

| Sandbox | Scenario |
| --- | --- |
| `longmem-mini-direct` | Direct memory lookup |
| `longmem-mini-update` | Stale update / latest fact |
| `longmem-mini-abstain` | Missing information / abstention |

The aggregate result is written to:

- `runs/latest/parallel_islo_results.json`
- `site/assets/parallel_islo_results.json`

Result:

```text
update_aware_memory: 3/3
keyword_memory: 2/3
no_memory: 1/3
```

## Run Locally

```bash
python demo.py
```

Expected output:

```text
Tiny LongMemEval-style benchmark on Islo
This is a miniature deterministic demo, not an official LongMemEval score.

Leaderboard
- update_aware_memory: 3/3 (100%)
- keyword_memory: 2/3 (67%)
- no_memory: 1/3 (33%)
```

The script writes:

- `runs/latest/results.json`
- `site/assets/results.json`

## Run on Islo

The Islo CLI is authenticated on this machine and `islo.yaml` validates. A small parallel eval was run across three Islo Python sandboxes and saved in `runs/latest/parallel_islo_results.json`.

After publishing the repo to GitHub:

```bash
islo use longmem-mini --source github://zozo123/longmem-mini-on-islo
python demo.py
python -m http.server 8080 -d site
islo share longmem-mini 8080 --public --ttl 24h
```

That gives you a public one-page result board backed by the same generated JSON.

## Run as a Harbor Task

Harbor is the evaluation wrapper. The direct Python script is the demo; Harbor makes it look like a real benchmark task.

```bash
harbor run -p harbor/longmem-mini -a oracle
```

On Islo:

```bash
harbor run -p harbor/longmem-mini -a oracle --env islo
```

The Harbor verifier runs the same tiny benchmark and writes `/logs/verifier/reward.txt`.
Local Harbor runs require Docker to be running. On this machine, the local Harbor command reached Harbor but could not start because Docker was not running.

The currently installed Harbor CLI here does not expose `islo` as an environment option. The task wrapper is still included so the repo is ready for a Docker-backed Harbor run or a Harbor build that exposes the Islo environment.

See `EVAL_REPORT.md` for the exact run status.

## Why This Is Good

Terminal-Bench is great for terminal/tool-using agents, but retrieval and long-term memory need different smoke tests. This demo compresses the long-memory problem into a tiny artifact:

- It distinguishes "found something" from "found the current thing."
- It includes abstention, which many toy RAG demos skip.
- It produces deterministic JSON, so a one-page result board can be checked into GitHub Pages.
- It maps cleanly to Islo and Harbor without requiring the full LongMemEval dataset.

The scale-up path is straightforward: replace the 3 handcrafted questions with LongMemEval or LoCoMo tasks, then use Harbor + Islo to run isolated trials in parallel.

## GitHub One-Pager

The page lives in `site/index.html`. After running `python demo.py`, publish `site/` with GitHub Pages or a separate `zozo123.github.io/<project>` page repo.

Suggested HN title:

```text
Show HN: Tiny long-memory benchmark running in an Islo sandbox
```
