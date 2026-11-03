# Two-case data and environment pilot

The pilot selects benchmark case 100 (five-task linear route ranking) and case 053
(six-task player recovery, with three independent summary branches). Authored Dagster
controls live under `pilots/route_linear` and `pilots/player_fanout`. Both consume the
actual visible `inputs/data.csv`, produce every required intermediate/final artifact,
and preserve the reviewed task/dependency graph. These controls exercise the harness;
they are not LLM generations or paper evaluation results.

Run from this repository after building the documented runtime image:

```sh
python tools/qualify_benchmark_pilot.py \
  --benchmark-root /absolute/path/to/benchmark-v1 \
  --output qualification-runs/new-real-data-pilot
```

The benchmark location is an explicit input, not an application dependency. The
harness copies inputs and candidate code, runs the existing behavioral references
in a separate control container, constructs evaluator-owned graph/artifact/oracle
specifications, and invokes the same evaluator used by experimental submissions.
References and expected answers are mounted only into the control phase and never
into the candidate container. Expected outputs for this smoke test are regression
comparisons to the existing references; they do not establish independent oracle
validity or full invalid-input behavior. Independent benchmark assertions remain
necessary before paper scoring.

## Fixed filesystem interface

```text
Host case directory                   Candidate container
candidate/definitions.py        -->   /candidate/definitions.py     read only
inputs/data.csv                 -->   /inputs/data.csv              read only
private/evaluation.json               not mounted
private/expected/                     not mounted
fresh output directory          -->   /outputs/                     writable
public entry configuration      -->   /protocol/runtime.json        read only
fresh evidence directory        -->   /evidence/                    writable
```

The entry module is `definitions`, the exported attribute is `defs`, and data paths
come from `SERVICECRAFT_INPUT_DIR` and `SERVICECRAFT_OUTPUT_DIR`. Scripts write only
beneath the output directory. Package/module names can vary through the spec; a
pipeline is not required to adopt these example source filenames. Every attempt
gets new outputs, snapshots, hashes and Dagster storage. No previous outputs are
used as candidate input.

## Environment gate before scoring

The specification declares evaluator-approved distribution versions in
`required_packages` and module names in `required_imports`. The pilot requires
Dagster 1.13.12, NumPy 2.0.1 and pandas 2.2.2. A dedicated container checks installed
versions and actually imports those modules before candidate code is loaded.
The report records `environment.checks` and `environment.log`.

* An unavailable/mismatched approved package or broken approved import produces
  `infra_error` and null scores. Fix/requalify the environment, then rerun according
  to the experiment's declared infrastructure policy.
* A candidate using an undeclared/unpermitted dependency fails as a candidate.
  Do not install packages reactively for individual generated submissions.
* Preflight is a smoke test, not a proof of every native-library behavior. A trusted
  reference execution in the exact image also acts as the case-level control. A
  subsequently suspected environment defect should trigger that control and a
  recorded audit rather than an automatic reclassification of all import failures.

For the full experiment, assign dependency profiles before generation (e.g. table
analytics, ML, plotting, geospatial), build locked evaluator-owned images, and run
trusted controls for every assigned case/profile before freezing the experiment.
Use the same approved profile for both methods on a case. Supply that package list
and filesystem contract in both prompts. Preserve the resolved image ID, package
freeze and preflight evidence. Execution stays offline; dependency installation
happens during image construction.

## Observed result

The initial real-data pilot passed both controls: executability, contracts,
behavioral regression and complete success were all 1. Deliberately requiring the
wrong Dagster version produced an infrastructure error and null scores. See
`benchmark-pilot-summary.json`; full local evidence is under
`qualification-runs/real-data-pilot-01/`.
