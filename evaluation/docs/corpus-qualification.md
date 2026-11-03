# Full-corpus control and oracle qualification

The source benchmark has 100 numbered cases. ServiceCraft's `corpus/registry.json`
records a control, an approved dependency profile, artifact oracles, independent
assertions and runtime evidence for each. It preserves the source benchmark's
author-review field rather than signing off on the author's behalf.

## Verified qualification results

The 0.6.0 qualification covers **100/100 controls** and **651 declared artifacts**:
472 CSVs, 132 JSON files and 47 serialized models. All controls passed isolated
Dagster execution, artifact comparisons and the independent assertions. All 100
cases rejected a missing required input column and a missing required output;
all 47 model artifacts passed behavioral probes and rejected corrupted model files.
Every case has an assigned, image-pinned `scientific-v1` dependency profile.

The release also passed 32 unit tests, 18 Docker regression scenarios and a
two-case batch admission/execution smoke test using the assembled corpus.
See `corpus/qualification-summary.json` for totals and `corpus/registry.json`
for per-case paths, hashes, mappings and evidence. The corpus has 69 distinct
reference-code fingerprints; these are implementation groups, not a reviewed
classification of independent task families. All 100 author semantic-review
flags remain pending.

## What the controls execute

Three sources already expose separate task functions; their Dagster assets invoke
those functions at the declared artifact boundaries. Other sources combine several
logical tasks in one reference function. The conservative control adapter extracts
statement dependencies and observable artifact-publication checkpoints, then
executes the relevant computation in each Dagster asset. Upstream state is passed
through actual asset inputs with an in-memory IO manager. Models are fitted at
their model stage, branches compute their own summaries, and declared joins receive
their parent results. Whole-pipeline reference replay per task and empty placeholder
assets are not used.

The adapter retains validation guards and handles mutable state, variable
reassignment, nested helper globals, comprehension scopes and file-handle scopes.
It rejects unsupported publication boundaries and hidden cross-task publications.
Every logical task must publish its declared current-run artifacts. The generated
`plan.json` exposes statement sources, dependencies and task targets for inspection.
The original formulas and helper implementations remain visible in `support.py`.
These are trusted controls, never generated submissions or candidate repair.

Nine logical graphs use the task identifier `context`, which is reserved by
Dagster. The control uses the physical asset name `context_features`; each registry
entry records the explicit logical-to-asset mapping. Original task graphs retain
their logical identifiers.

## Oracle coverage

CSV and JSON artifacts are compared against freshly generated reference outputs
with declared tolerances, preserving required rows, columns and order. The private
oracle container also executes each case's existing independently calculated
invariants from the benchmark qualification scripts. It validates every source
graph's schema, topology, artifact bindings and fixture hashes.

Serialized model files receive behavioral probes in an isolated container. The
oracle loads the trusted and candidate model, selects raw feature columns from a
trusted reference table and compares predictions or class probabilities on up to
256 evenly spaced eligible rows. Supported model interfaces are a scikit-learn
estimator/Pipeline, or a bundle with `model`, optional `scaler`, `features`, and
optional `mapping`/`canonical_mapping` for canonical cluster labels. Clustering
probes account for the recorded label mapping. Publish this serialization contract
equally to both generation methods before scored runs.

The oracle image has additional pinned JSON Schema dependencies. Oracle code,
expected values, source metadata and model probe tables remain outside candidate
runtime containers. Loading a candidate pickle happens only in the restricted
oracle container, never in the operator process. Full private oracle diagnostics
must not be supplied to an LLM repair loop; use separate development diagnostics.
This is functional evaluation under the documented non-adversarial-code assumption,
not tamper-proof attestation of malicious serialized objects.

## Negative qualification

For every case, remove a required source column and require the valid Dagster
definition to reject execution. For cases with models, corrupt every serialized
model and require the model oracle to reject every corrupted file. Also remove a
mandatory output and verify that this is a candidate failure, not an infrastructure
error. The original input files and successful evidence remain unchanged.

The uniform private oracle snapshot is rerun against every successful control's
saved artifacts before the registry is finalized. A failed positive/negative probe
marks the case unadmitted. Human author review remains a separate recorded field.

## Reproduce

Run these commands from `evaluation/` after activating the root environment.
Build the runtime first, then the oracle image. The oracle Dockerfile accepts
`RUNTIME_IMAGE` as a build argument, defaulting to the local runtime tag. New
builds/platforms require new qualification; historical local image IDs are not
registry manifest digests or approval for a rebuilt image.

```sh
docker build -t servicecraft-runtime:1.13.12 .
docker build -f Dockerfile.oracles -t servicecraft-oracle:corpus-v1 .
python tools/prepare_corpus.py --benchmark-root ../corpus --output prepared-controls
python tools/qualify_corpus.py --benchmark-root ../corpus --prepared prepared-controls --output qualification-runs/corpus-new --workers 3
python tools/assemble_corpus.py --benchmark-root ../corpus --prepared prepared-controls --qualifications qualification-runs/corpus-new --output qualified-corpus
python tools/probe_corpus_controls.py --corpus qualified-corpus --benchmark-root ../corpus --output qualification-runs/corpus-negative-new --workers 3
python tools/summarize_corpus.py --corpus qualified-corpus
```

Fresh output directories are required. During development, multiple qualification
directories can be supplied to the assembler: successful, fully evidenced corrections
replace failed earlier attempts, which remain intact. Source hashes must match
the successful control report before an adapter can be assembled.

## Layout and experimental use

```text
corpus/
  registry.json
  control-smoke-experiment.json
  cases/<case-id>/
    candidate/             Trusted Dagster control and stage plan
    inputs/                Versioned visible fixture copy
    evaluation.json        Evaluator-owned specification
    private/               Expected artifacts and isolated oracle context
    qualification/         Successful logs, events and output artifacts
```

Operator input fixtures and private answers/oracle contexts are included in Git.
Raw historical qualification evidence is ignored and can be regenerated with the
commands above. `summarize_corpus.py` requires that freshly generated evidence;
it is not a fresh-clone-only inventory command.
Never mount an entire case folder into a generator: generation inputs still come
from the existing natural-language/fixed-graph allowlist exports. Only `candidate/`
and `inputs/` are mounted into the scored runtime.

`control-smoke-experiment.json` exercises trusted controls through the batch
admission mechanism; its entries are not LLM experimental observations. For main
runs, replace entries with actual submissions, retain the case control/profile,
and use a reviewed runtime node mapping. The supplied specification is tailored
to the control's physical asset names. Semantic RQ1 matching and alternative valid
task decompositions still need their own qualified mapping procedure.

The qualified checks use the current visible fixtures. They establish runtime and
oracle readiness for those fixtures, not unseen-input generalization or a complete
proof of all prose requirements. Preserve author semantic signoff, declared
development/test splits and any additional held-out-fixture qualification before
making the paper's final claims. Reused reference implementations also mean that
100 numbered cases should not automatically be treated as 100 independent task
families in statistical analysis.
