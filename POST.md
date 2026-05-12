# Show HN Draft

## Title

Show HN: Tiny long-memory benchmark running in an Islo sandbox

## Short Post

I made a tiny LongMemEval-style benchmark that runs in seconds, is packaged as a Harbor task, and was fan-out tested across three Islo sandboxes.

It compares three simple memory approaches:

- `no_memory`: no persisted chat history, so it abstains.
- `keyword_memory`: retrieves the best keyword-overlap session.
- `update_aware_memory`: retrieves relevant sessions, prefers newer facts for update questions, and abstains when evidence is missing.

The benchmark has only three questions:

1. Direct lookup: remember a snack preference.
2. Knowledge update: use the latest airport after an earlier airport became stale.
3. Abstention: refuse to answer a jacket-size question that is not in memory.

The result is intentionally simple:

```text
update_aware_memory: 3/3
keyword_memory: 2/3
no_memory: 1/3
```

The Islo part is the interesting runtime shape: one tiny scenario per sandbox, launched in parallel from a local script:

```bash
python3 parallel_islo_eval.py --backend islo --prefix longmem-mini
```

That creates/reuses:

```text
longmem-mini-direct
longmem-mini-update
longmem-mini-abstain
```

The point is not to claim a leaderboard score. It is a small, inspectable demo of what long-memory evaluation needs to test: not just whether retrieval finds something, but whether it finds the current thing and knows when nothing is there.

Harbor is used as the evaluation wrapper. The repo includes a minimal Harbor task with `task.toml`, `instruction.md`, `environment/Dockerfile`, `tests/test.sh`, and `solution/solve.sh`. The verifier runs the benchmark, checks the expected mini leaderboard, and writes `/logs/verifier/reward.txt`.

Islo is used as the execution and sharing layer. The repo includes `islo.yaml`, so the benchmark can run in clean Python sandboxes. I ran the three simple scenarios across three Islo sandboxes and got the same `3/2/1` aggregate result. The static result page can be served from a sandbox and exposed with `islo share`.

One implementation note: this machine's local Harbor run could not complete because Docker was not running, and the installed Harbor CLI here does not expose `islo` as an environment option. So the honest claim is: local Python eval completed, parallel Islo scenario eval completed, and Harbor packaging/verifier are included for the eval wrapper path.

This is deliberately not full LongMemEval. The next step would be replacing the three handcrafted questions with LongMemEval or LoCoMo tasks and using Harbor + Islo to run isolated trials in parallel.

## Commands

```bash
python demo.py
python3 parallel_islo_eval.py --backend islo --prefix longmem-mini
```

```bash
harbor run -p harbor/longmem-mini -a oracle
harbor run -p harbor/longmem-mini -a oracle --env islo
```

```bash
islo use longmem-mini --source github://zozo123/longmem-mini-on-islo
python demo.py
python -m http.server 8080 -d site
islo share longmem-mini 8080 --public --ttl 24h
```
