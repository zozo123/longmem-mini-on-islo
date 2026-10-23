# Tiny Long-Memory Benchmark on Islo

A toy, deterministic [LongMemEval](https://github.com/xiaowu0162/LongMemEval)-style demo ([paper](https://arxiv.org/abs/2410.10813)) by Yossi Eliaz, May 2026: three hand-written memory strategies answer three handcrafted questions, run in islo.dev sandboxes and packaged as a [Harbor](https://github.com/harbor-framework/harbor) task.

This is **not** an official LongMemEval score. It is a small, inspectable demo for anyone curious why long-memory systems need to handle retrieval, updates, and abstention.

Project page: https://zozo123.github.io/longmem-mini-on-islo/

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

The goal is not to win a benchmark. The goal is to make the failure modes obvious.

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

`islo.yaml` validates. A small parallel eval was run once (2026-05-12) across three Islo Python sandboxes and saved in `runs/latest/parallel_islo_results.json`.

```bash
islo use longmem-mini --source github://zozo123/longmem-mini-on-islo
python demo.py
python -m http.server 8080 -d site
islo share longmem-mini 8080 --public --ttl 24h
```

That gives you a public one-page result board backed by the same generated JSON.

## Run as a Harbor Task

Harbor is the evaluation wrapper. The direct Python script is the demo; Harbor packages it as an eval task.

```bash
harbor run -p harbor/longmem-mini -a oracle
```

The Harbor verifier runs the same tiny benchmark and writes `/logs/verifier/reward.txt`.
The Harbor task is packaged but has not been run end to end (local Docker was unavailable when this was built).

The Harbor CLI version used to build this did not list `islo` as an environment option, so there is no Harbor-on-Islo run. The task wrapper is included for a Docker-backed Harbor run or a Harbor build that exposes an Islo environment.

See `EVAL_REPORT.md` for the exact run status.

## What the demo shows

Terminal-Bench is great for terminal/tool-using agents, but retrieval and long-term memory need different smoke tests. This demo compresses the long-memory problem into a tiny artifact:

- It distinguishes "found something" from "found the current thing."
- It includes abstention, which many toy RAG demos skip.
- It produces deterministic JSON, so a one-page result board can be checked into GitHub Pages.
- It maps cleanly to Islo and Harbor without requiring the full LongMemEval dataset.

The scale-up path is straightforward: replace the 3 handcrafted questions with LongMemEval or [LoCoMo](https://github.com/snap-research/locomo) tasks, then use Harbor + Islo to run isolated trials in parallel.
