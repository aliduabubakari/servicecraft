# ServiceCraft Evaluation

Standalone tooling for the ServiceCraft paper's empirical analysis of generated
Dagster pipelines. It evaluates submissions from any generation method through
the same six stages:

1. Submission/layout validation.
2. Static source measurements and direct scaling.
3. Dagster definitions and dependency graph validation.
4. Isolated Docker execution.
5. Intermediate/final artifact contracts.
6. Independent behavioral comparisons against private expected outputs.

The primary outcome is binary complete implementation success. Raw measurements,
scaled static metrics, graph comparisons, events and errors explain each result.
This project has no dependency on the InLumen application, deployment validator,
code generation service, or any sibling repository. An application is simply one
of the methods that can submit Dagster code.

Version 0.6.0 includes qualified controls, private oracles and pinned dependency
profiles for all 100 benchmark cases. Qualification passed for 651 artifacts,
including behavioral checks on 47 serialized models, plus deliberate input,
output and model failures. Release checks passed 32 unit tests, 18 Docker
regression scenarios and a two-case corpus batch smoke test. See the
[corpus qualification guide](docs/corpus-qualification.md) for evidence and
reproduction. These are visible-fixture control results; author semantic
review remains pending.

All cases also provide a standardized `prompt.txt` for automated generation;
see [task prompt usage](docs/corpus-prompts.md) for safe exports and synchronization.

## Install and evaluate

Requirements: Python 3.11+, a running Docker engine, and a locally built runtime
image. From this repository:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e .
docker build -t servicecraft-runtime:1.13.12 .

python -m app.service_craft eval examples/sum/candidate \
  --inputs examples/sum/inputs \
  --spec examples/sum/private/evaluation.json \
  --report-dir qualification-runs/example \
  --metadata '{"method":"example","model":"none","track":"fixed_graph","attempt":0}'
```

The installed command `service-craft eval ...` has the same arguments. The report
directory must be new. The candidate directory and input directory contain only
allowed submission materials; the private specification and oracle files remain
outside both directories. Exit codes: 0 complete success, 1 candidate failure,
2 evaluation setup/infrastructure error. Infrastructure errors have unavailable
(`null`) scores and follow the experiment's declared rerun policy.

See [evaluation protocol](docs/evaluation.md), [measurement definitions](docs/metrics.md),
the [input schema](schemas/evaluation-spec.schema.json), and
[result schema](schemas/evaluation-result.schema.json).

See the [two-case real-data pilot](docs/benchmark-pilot.md) for runnable Dagster
controls, data mounts, approved dependency preflight and experiment automation.

For the full automated workflow, see [batch experiment protocol](docs/automated-experiment.md):
`python -m app.service_craft batch experiment.json --output runs/experiment-01`.
It adds case controls, frozen runtime profiles, resumable evidence, infrastructure
retries, and JSONL/CSV exports over every scheduled evaluation.

The [full-corpus guide](docs/corpus-qualification.md) describes all 100 trusted
controls, private independent/model oracles, dependency assignments, reproduction
commands and admission evidence in `corpus/registry.json`.

Version 0.5.0 passes **23 tests**, **18 Docker regression cases**, and a real-data
batch integration test covering two successes, two candidate failures and one
blocked environment. See [automation qualification](automation-qualification-summary.json).

## Static measurements: direct scaling, no custom weights

| Measurement | Scaled value | Direction |
| --- | --- | --- |
| Flake8 | Distinct source lines with findings / physical Python source lines | Lower is better |
| Pylint | Distinct source lines with messages / physical Python source lines | Lower is better |
| Bandit | Distinct source lines with findings / physical Python source lines | Lower is better |
| Radon maintainability index | Native file MI / 100; also report the arithmetic mean across files | Higher is better |

All counts, Pylint message types, Bandit severities, file maintainability indices,
and mean/maximum cyclomatic complexity remain available as raw measurements.
Complexity is unbounded and is reported in its original units. There is no combined
static score, severity weighting, fitted threshold, legacy five-dimension SAT, or
calibration stage. The metric version is `servicecraft.raw-static@1`.

## Qualification

```sh
pip install -e '.[test,analysis]'
python -m pytest -q
python tools/qualify_evaluator.py qualification-runs/new-run
```

Qualification runs genuine Dagster containers for valid graph topologies and
deliberate syntax/import/definition/runtime/timeout/graph/output/check failures.
The generated cases are development fixtures for the evaluator, rather than
empirical results for the paper's benchmark corpus. Full evidence stays in the
chosen run directory; `qualification-summary.json` records the checked revision.

The initial standalone 0.4.0 revision passed **15 tests and 18 real Docker qualification
cases**. Its installed module CLI also passed the example when invoked outside
the repository directory. See [qualification summary](qualification-summary.json)
for the runtime image identity and source hashes. Full local evidence is under
`qualification-runs/servicecraft-v1`.

## Optional local API

```sh
pip install -e '.[api]'
uvicorn app.main:app --host 127.0.0.1 --port 8020
```

`POST /evaluate` accepts `candidate_path`, `inputs_path`, `spec_path`, `report_dir`,
and optional `metadata`. `GET /health` identifies ServiceCraft and its version.
The API is for the experiment operator: its paths refer to the operator host.
Generation and application-specific bundle repair belong to the submitting method.

## Repository layout

This evaluator is the `evaluation/` package of the standalone ServiceCraft repository.
Run commands in this guide from `evaluation/` after activating the repository-root
virtual environment. Install with `python -m pip install -e './evaluation[test,corpus]'`
from the repository root. The benchmark source is `../corpus`; no InLumen
application or code generation service is required. See the [root README](../README.md)
for fresh-clone setup, included scoring fixtures and experiment boundaries.
