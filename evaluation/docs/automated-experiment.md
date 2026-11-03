# Automated experiment runs

Use `python -m app.service_craft batch experiment.json --output runs/experiment-01`
for paper runs. `eval` remains available for debugging one submission. The batch
runner uses the same six-stage evaluator, with experiment-level admission controls,
frozen dependency profiles, resume validation, and complete result exports.

## Prepare before running

1. Qualify each case's reference behavior and private oracles independently.
2. Prepare a known-good Dagster control for every case/input fixture. The control
   uses the same approved profile as the experimental submissions on that case.
3. Assign a dependency profile before generation. Build its locked runtime image;
   supply the same filesystem and dependency contract to both methods.
4. Save every generated submission separately, including failed generation outputs
   when available, then create one manifest entry per scheduled evaluation.

The shipped scientific profile is in `profiles/scientific.json`. Copy that object
into the manifest's `profiles` map; additional profiles use the same shape. A
profile overrides the image/packages/imports in individual evaluation specs. This
prevents different methods from silently receiving different runtime policies.
These declarations are health checks for the approved image, rather than a source
import allowlist. Publish the complete installed package list to both methods;
packages outside the checked subset may also be available in the image.

## Manifest

All filesystem paths are relative to the manifest location, or absolute:

```json
{
  "schema_version": "servicecraft.experiment@1",
  "profiles": {
    "tables": {
      "image": "servicecraft-runtime:1.13.12",
      "required_packages": {"dagster":"1.13.12","pandas":"2.2.2","numpy":"2.0.1"},
      "required_imports": ["dagster","pandas","numpy"]
    }
  },
  "controls": {
    "case_100": {
      "profile": "tables",
      "candidate": "controls/100/candidate",
      "inputs": "cases/100/inputs",
      "spec": "cases/100/private/evaluation.json"
    }
  },
  "entries": [
    {
      "id": "case100_direct_modelA_rep0",
      "control": "case_100",
      "candidate": "submissions/100/direct/modelA/rep0",
      "inputs": "cases/100/inputs",
      "spec": "cases/100/private/evaluation.json",
      "metadata": {"method":"direct","model":"modelA","track":"fixed_graph","repetition":0,"attempt":0}
    }
  ],
  "infrastructure_retries": 1
}
```

Entries must reference a control with the same case ID and identical input hashes.
Expected task/asset mapping can be expressed by each evaluator-owned specification.
Do not give these private specifications or controls to the generation methods.

## Execution and recovery

At startup, the runner resolves each image tag to its immutable ID and records
`experiment-lock.json`: manifest, approved profiles, candidate/input hashes,
normalized private specifications, oracle hashes and evaluator source hashes.
Controls execute before any scored submissions. An unsuccessful control blocks
its associated submissions as `blocked_control`, with unavailable scores. The
control's report under `controls/` explains the failure.

For admitted cases, package versions and actual imports are checked in the pinned
container before loading generated code. Missing benchmark inputs, a failed
approved environment or evaluator errors produce infrastructure results with null
scores. Candidate syntax/import/runtime/output failures produce candidate zeros.
An undeclared dependency is not installed on demand. Suspected defects in a
qualified environment require a recorded control audit, rather than silently
changing the image or relabeling every generated import error.

`infrastructure_retries` applies only to unavailable infrastructure results, with
each retry retained in `try-00`, `try-01`, etc. It never repairs/regenerates code or
retries candidate zeros. Generation/repair attempts belong in separate manifest
entries. Exhausted unavailable results remain in the exports for the declared rerun
and analysis policy. Deterministic environment mismatches may need operator repair
and a new experiment output, rather than repeated retries.

Resume with:

```sh
python -m app.service_craft batch experiment.json --output runs/experiment-01 --resume
```

Resume rejects changes to the locked manifest, images, evaluator sources, inputs,
submissions or private oracles. Completed reports are reused without executing
containers again. Partially written attempt directories are preserved with an
`interrupted` suffix before a replacement execution. Keep source fixtures immutable
throughout a run. Run one batch process per output directory; execution is currently
sequential. Parallel experiment shards need distinct output directories.

## Results

* `controls/<id>/try-NN/`: control reports and evidence.
* `entries/<id>/try-NN/`: every scored attempt and infrastructure retry.
* `summary.json`: incremental checkpoint after each processed entry.
* `results.jsonl`: one row per scheduled entry, including metadata, stage statuses,
  static measurements, binary scores and report location.
* `results.csv`: binary analysis table; empty score cells mean unavailable, not zero.

Exit code 0 means all scheduled entries succeeded; 1 means candidate failures;
2 means setup failure or at least one unavailable/blocked result. Every scheduled
entry appears in a completed batch's exports. The runner does not silently remove
blocked cases, calculate a success rate on survivors, or pool experiment tracks.
Retain initial/final generation checkpoints separately and define infrastructure
reruns and paper denominators before the main study.

Runtime definition evidence is checkpointed before execution so timeouts retain
the already validated graph. Structured results are validated and atomically saved.
The runner measures evaluation wall-clock time. Generation tokens/costs still
require instrumentation in the experiment's generation driver.

## Repeatable qualification

```sh
python -m pytest -q
python tools/qualify_evaluator.py qualification-runs/new-regression
python tools/qualify_benchmark_pilot.py --benchmark-root /path/to/benchmark-v1 --output qualification-runs/new-pilot
python tools/qualify_automation.py --pilot-dir qualification-runs/new-pilot --output qualification-runs/new-automation
```

The automation qualification runs both real-data controls, two successful entries,
an undeclared-import failure, a valid-execution/wrong-output failure, and a broken
approved environment. It verifies all five scheduled entries remain visible and
that resume reuses completed evidence. These are authored/injected controls, not
LLM experiment results. All 100 cases now have historically qualified controls, oracle coverage and
assigned profiles; requalify changed environments before main-study admission.
Author semantic review remains pending.
