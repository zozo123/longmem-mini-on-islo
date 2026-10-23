# Evaluation Report

This repo contains a tiny LongMemEval-style benchmark, not an official LongMemEval run.

The purpose is to show the mechanics of a long-memory eval in a form that is small enough to inspect:

- 5 synthetic chat sessions
- 3 questions
- 3 simple memory approaches
- deterministic scoring
- parallel Islo scenario fan-out
- Harbor task wrapper
- Islo sandbox run path

## What Was Evaluated

| Approach | Behavior | Score |
| --- | --- | --- |
| `no_memory` | No persisted history; abstains. | `1/3` |
| `keyword_memory` | Retrieves the top keyword-overlap session. | `2/3` |
| `update_aware_memory` | Prefers newer relevant facts for update questions and abstains when evidence is missing. | `3/3` |

## Questions

| Ability | Question | Expected |
| --- | --- | --- |
| Direct lookup | What snack should I buy for Mira's study group? | `sea-salt pistachios` |
| Knowledge update | For the Portland trip, which airport should I use now? | `OAK` |
| Abstention | What is Sam's jacket size? | `not enough information` |

## Runs Completed

### Local Python Eval

Command:

```bash
python3 demo.py
```

Result:

```text
Tiny LongMemEval-style benchmark on Islo
This is a miniature deterministic demo, not an official LongMemEval score.

Leaderboard
- update_aware_memory: 3/3 (100%)
- keyword_memory: 2/3 (67%)
- no_memory: 1/3 (33%)
```

Artifacts:

- `runs/latest/results.json`
- `site/assets/results.json`

### Parallel Islo Scenario Eval

The Islo CLI is authenticated and `islo.yaml` validates. Three Python sandboxes were created/reused, one per simple eval scenario:

| Sandbox | Scenario |
| --- | --- |
| `longmem-mini-direct` | Direct memory lookup |
| `longmem-mini-update` | Knowledge update |
| `longmem-mini-abstain` | Abstention |

Command:

```bash
python3 parallel_islo_eval.py --backend islo --prefix longmem-mini
```

Artifacts:

- `runs/latest/parallel_islo_results.json`
- `site/assets/parallel_islo_results.json`

Result:

```text
- update_aware_memory: 3/3 (100%)
- keyword_memory: 2/3 (67%)
- no_memory: 1/3 (33%)
```

This is the core Islo demo: independent scenarios can run in isolated sandboxes and be aggregated by a simple local collector.

## Harbor Status

The repo includes a minimal Harbor task wrapper:

```text
harbor/longmem-mini/
  task.toml
  instruction.md
  environment/Dockerfile
  environment/demo.py
  tests/test.sh
  solution/solve.sh
```

The Harbor verifier runs the benchmark, checks the expected mini leaderboard, and writes:

```text
/logs/verifier/reward.txt
```

Attempted local Harbor command:

```bash
harbor run -p harbor/longmem-mini -a oracle
```

Result: the command reached Harbor, but Docker was not running on this machine, so the local Docker environment could not start.

Attempted Harbor Islo command:

```bash
harbor run -p harbor/longmem-mini -a oracle --env islo
```

Result: the currently installed Harbor CLI in this environment does not expose `islo` as an environment option. Its available environments are `docker`, `daytona`, `e2b`, `modal`, `runloop`, and `gke`.

In short:

- The small eval was run locally and across three Islo sandboxes.
- The benchmark is packaged as a Harbor task.
- The Harbor wrapper is ready for a Harbor environment with Docker running, or a Harbor build that exposes the Islo environment.

## Why This Is Still Useful

This is enough for a demo because the point is the eval shape, not leaderboard scale. The artifact shows:

- how stale retrieval fails on updated memories
- how abstention is scored
- how deterministic results can feed a one-page report
- how the same fixture can be wrapped as a Harbor task
- how Islo can run scenario trials in parallel and share the runnable demo

The scale-up path is to replace the 3 handcrafted questions with LongMemEval or LoCoMo tasks and run them through Harbor on an execution backend.
