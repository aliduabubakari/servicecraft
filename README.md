# ServiceCraft

A benchmark corpus and independent evaluator for studying how language-model
methods construct executable **Dagster** data pipelines. ServiceCraft supports
comparisons between direct generation, InLumen and coding agents using the same
task inputs and evaluation protocol. No InLumen application or service is needed
to install or run this repository.

The repository contains **100 cases**, versioned natural-language prompts, local
input fixtures, task/dependency specifications, trusted Dagster controls, artifact
contracts and behavioral oracles. Evaluation records static diagnostics and a
six-stage correctness ladder, ending in **complete implementation success: 0 or 1**.

## Repository map

```text
corpus/                         Benchmark source specifications and fixtures
  pipelines/<case-id>/
    prompt.txt                  Standardized generation task
    description.md              Source task requirements
    inputs/                     Public input fixtures
    task_graph.json             Evaluator-owned task/dependency specification
    reference.py                Trusted behavioral reference
    provenance.json             Upstream source and fixture provenance
  tools/                        Export, prompt publication and qualification tools
  prompt-manifest.json          Prompt/template hashes for all cases
evaluation/                     Installable standalone Python evaluator
  app/                          CLI, static analysis, Docker runtime and oracles
  corpus/cases/<case-id>/        Runnable evaluation fixtures
    candidate/                  Trusted Dagster control, not an LLM submission
    inputs/                     Evaluation fixture copy
    evaluation.json             Private evaluation specification
    private/                    Expected artifacts and independent oracle context
    prompt.txt                  Exact copy of the source corpus prompt
  examples/sum/                 Small runnable fan-in example
  schemas/                     Machine-readable experiment/result contracts
  profiles/                    Approved runtime dependency declarations
  tests/                       Evaluator unit and integration tests
docs/                           Repository workflow and migration notes
AGENTS.md                       Instructions for AI development tools
```

The two corpus directories serve different purposes: `corpus/` defines the
benchmark, while `evaluation/corpus/` packages its trusted runtime controls and
scoring fixtures. Reference answers are included for experiment operators.
**Never give a benchmarked coding agent access to this entire repository.**
Generate a separate allowlisted workspace as shown below.

## Quick start

Requirements: Python **3.11+**, Git, and a running Docker engine for runtime
evaluation. Commands below run from the repository root unless stated otherwise.

```sh
git clone https://github.com/aliduabubakari/servicecraft.git
cd servicecraft
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e './evaluation[test,corpus]'

docker build -t servicecraft-runtime:1.13.12 evaluation
docker build -f evaluation/Dockerfile.oracles \
  -t servicecraft-oracle:corpus-v1 evaluation

python -m app.service_craft --version
python -m app.service_craft eval evaluation/examples/sum/candidate \
  --inputs evaluation/examples/sum/inputs \
  --spec evaluation/examples/sum/private/evaluation.json \
  --report-dir runs/example-01 \
  --metadata '{"method":"trusted_example","model":"none","track":"fixed_graph"}'
```

The example implements a fan-in graph, generates JSON artifacts and checks their
values. Inspect `runs/example-01/result.json`, the stage evidence and runtime
logs. The report directory must be new; choose another name to rerun. The
installed `service-craft` command is equivalent to `python -m app.service_craft`.

Use an installed Python 3.11+ executable (for example `python3.12`) for the venv
command if `python3.11` is unavailable. macOS system `python3` may be older.

| Exit code | Meaning |
| --- | --- |
| 0 | Complete implementation success |
| 1 | Candidate failed at least one required check |
| 2 | Setup or infrastructure failure; correctness scores are unavailable |

## Obtain a task for generation

Each case has seven prompt sections: objective, available inputs, processing,
dependency/topology requirements, outputs, execution/numerical rules and deliverable.
Use the same `prompt.txt` for every compared method and supply a separately frozen
shared runtime/submission contract. Do not send the source description a second
time; the rendered prompt already preserves its task-specific requirements.

Export a fresh natural-language workspace outside the repository:

```sh
python corpus/tools/export_inputs.py \
  016_sports_clustering_prediction_visualization /tmp/servicecraft-case016-nl \
  --track natural_language
```

The export contains `prompt.txt`, the compatibility `description.md`, and `inputs/`.
It excludes reference code, task graphs, expected outputs and private oracles.
The exporter refuses an existing destination and stale prompts. A coding agent
must be restricted to the exported workspace; an export alone does not sandbox
an agent that can read its parent filesystem.

For the implementation-only experiment, use `--track fixed_graph`. This adds
sanitized `provided_graph.json` intentionally. Keep the tracks separate:

| Track | Shared input | Intended measurement |
| --- | --- | --- |
| Natural language | Prompt, allowed inputs, shared runtime contract | Task/dependency design and end-to-end construction |
| Fixed graph | Those inputs plus reviewed graph/contracts | Implementation validity given the design |

An [example prompt](corpus/pipelines/016_sports_clustering_prediction_visualization/prompt.txt)
and the [source corpus guide](corpus/README.md) explain task contents and provenance.
Prompt/specification author semantic review is still pending.

## Evaluate a generated submission

Keep candidate source, allowed inputs and private evaluation data in separate
directories. Use an evaluator-owned specification to select the module, entry
point, expected graph, artifacts, checks and approved environment. For a full
example see [evaluation.json](evaluation/examples/sum/private/evaluation.json).

Evaluation proceeds through:

1. Submission and layout validation.
2. Static Python measurements with direct scaling.
3. Dagster definition and dependency-graph validation.
4. Isolated Docker execution.
5. Intermediate/final artifact contract checks.
6. Independent behavioral oracles.

The primary binary outcome requires all six stages to pass. A Docker process
exiting successfully does not by itself establish output correctness. Environment
failures have null scores rather than candidate zeros. Static measurements remain
separate diagnostics; there is no weighted aggregate quality score.

Runtime containers receive read-only source/inputs and writable run outputs; the
private oracle runs separately. See [filesystem and evaluation contract](evaluation/docs/evaluation.md),
[metrics](evaluation/docs/metrics.md) and [schemas](evaluation/schemas/).
Do not return private oracle diagnostics to a generation/repair loop.

## Automated batches and runtime qualification

```sh
python -m app.service_craft batch /path/to/experiment.json \
  --output runs/experiment-01
python -m app.service_craft batch /path/to/experiment.json \
  --output runs/experiment-01 --resume
```

Each entry refers to a trusted control and approved dependency profile. Batch
execution freezes source/input/specification hashes and runtime images, qualifies
controls before submissions, preserves every scheduled outcome, and writes JSONL
and CSV results. Resume rejects changes to the frozen inputs. See the
[batch manifest guide](evaluation/docs/automated-experiment.md).

The packaged control catalog records **historically qualified image IDs**. Those
local IDs need not exist on a new machine, and a new image build does not inherit
the prior qualification. Rebuild and requalify using the
[full-corpus workflow](evaluation/docs/corpus-qualification.md). That workflow
accepts this repository's `corpus/` as `--benchmark-root` and writes a new qualified
catalog. Keep historical records intact. The oracle Dockerfile accepts
`--build-arg RUNTIME_IMAGE=<tag-or-registry-digest>`; the batch runner resolves
actual images to immutable IDs. A local image ID is not a registry manifest digest.

## Check or update the corpus

Static analysis runs inside the Docker runtime. To exercise the optional host
static-analysis unit test as well, install `python -m pip install -e './evaluation[analysis]'`; otherwise that one test is skipped. CI installs this
extra. Docker regression tests are separate from CI's unit/corpus checks.

```sh
python corpus/tools/sync_prompts.py --evaluation-corpus evaluation/corpus --check
python corpus/tools/validate_specs.py
python -m unittest discover -s corpus/tools -p test_prompt_format.py -v
python -m pytest evaluation/tests -q
```

After editing an authoritative `description.md`, publish prompts with:

```sh
python corpus/tools/sync_prompts.py --evaluation-corpus evaluation/corpus
```

The renderer preserves source requirement paragraphs, inventories public input
headers, and reads no reference graph or private answer. Both prompt manifests
record the template/renderer version and per-case hashes. Changes to task behavior,
fixtures or contracts require semantic review and affected-case requalification;
format checks alone do not establish that descriptions and oracles agree.

For Docker regression checks, run from `evaluation/` after activating the root
environment:

```sh
cd evaluation
python tools/qualify_evaluator.py qualification-runs/new-regression
```

## Evidence and current limits

The imported 0.6.0 qualification reports record 100 passing controls, 651 artifacts
(472 CSV, 132 JSON, 47 serialized models), required-input/output rejection checks
for every case, and behavioral/corruption probes for all 47 models. These are
**visible-fixture control results**, not observations from LLM experiments or proof
of unseen-input generalization. See the [historical summary](evaluation/corpus/qualification-summary.json).

The standalone-repository migration additionally passed 32 evaluator tests, five
prompt tests, validation of all 100 specifications/prompt pairs, the Docker
quick-start example and fresh-image controls for cases 001 and 016. A Git-only
archive passed the unit/prompt checks without ignored working-tree fixtures.
See the [migration validation record](docs/repository-validation.json) for scope
and image identities.

The corpus includes seven topology classes and 69 distinct reference-code
fingerprints. Those fingerprints are not a reviewed set of independent semantic
families. Semantic task/dependency matching for alternative generated node
decompositions needs a reviewed mapping procedure. All 100 author semantic-review
flags remain pending.

The evaluator measures evaluation outcomes and elapsed time. A fully instrumented
generation driver for Direct/InLumen/Pi/Aider has not been implemented here.
Token accounting, generation latency, model-request/repair counts and cost need
collection in that driver. See the [method-comparison proposal](evaluation/docs/method-comparison-proposal.md).

Raw historical qualification logs and duplicated run artifacts are not committed;
the catalog retains provenance and summary records. Operator fixtures, expected
outputs and oracle contexts are included so evaluation can be reproduced. New
runs, exports, environments and credentials are ignored by Git.

## Provenance and AI tool use

The benchmark derives from [custom-pipelines](https://github.com/aliduabubakari/custom-pipelines).
Per-case provenance retains upstream commits, fixture hashes and revision rationale.
Read [provenance and licensing notes](NOTICE.md) before redistribution, and
[migration notes](docs/migration.md) for what was copied into this repository.
No new blanket license has been assigned to upstream material.

[AGENTS.md](AGENTS.md) explains repository commands, experiment boundaries and
change-validation rules for AI development tools. Its instructions distinguish
maintaining ServiceCraft from acting as a scored generation method.
