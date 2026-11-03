# Evaluation protocol

The operator supplies an evaluation specification with schema
`servicecraft.evaluation-spec@1`. It names the candidate's Python module, attribute,
project directory, and Python import paths. Assets, callable `Definitions`, and
native jobs (`mode: job`, `job_name`) use the same Docker runner.

The specification is evaluator-owned. It defines the required nodes, edges,
artifact contracts, and private output comparisons. Neither expected answers nor
the reference graph is mounted into a candidate's runtime container. Only runtime
entry settings and allowed run configuration are passed through.

## Runtime contract

Submissions receive:

* `SERVICECRAFT_INPUT_DIR=/inputs`
* `SERVICECRAFT_INPUT_MANIFEST=/inputs/input_manifest.json`
* `SERVICECRAFT_OUTPUT_DIR=/outputs`

The input directory need only contain an input manifest when the submission uses
one. `/outputs` is fresh for each attempt. `bundle_inputs` and `bundle_outputs`
optionally overlay existing candidate-relative subdirectories with allowed inputs
and fresh outputs, supporting projects with fixed relative paths. The evaluator
does not prescribe a generator's package name, bundle manifest or directory layout.

For an existing generator that expects different environment variable names, the
operator can explicitly map aliases in the specification:

```json
{
  "environment_aliases": {
    "LEGACY_INPUT_DIR": "input_dir",
    "LEGACY_OUTPUT_DIR": "output_dir"
  }
}
```

Aliases are optional, generator-neutral protocol settings. No application-specific
aliases are enabled by default. This preserves a candidate's existing interface
without introducing an application dependency or rewriting its computation.

The image pins Python's base image digest, Dagster 1.13.12, the analysis tools and
scientific dependencies. It records its full package freeze, image ID and platform.
Candidate dependency installation uses reviewed, prebuilt runtime images; arbitrary
generated Dockerfiles or install scripts are not executed. Missing imports are
definition failures. Use the same runtime/dependency policy for compared methods.

Each container runs as non-root, with no network, a read-only filesystem, restricted
capabilities, limited processes/CPU/memory and a wall-clock timeout. Inputs and
candidate sources are snapshots mounted read-only. Output and evidence directories
are unique per attempt. The candidate receives no Docker socket.

## Six stages and verdicts

1. Verify submission paths, regular files, Python source and optional bundle mounts.
2. Parse sources and collect raw/scaled static metrics.
3. Load Dagster definitions, validate configuration, build an execution plan and
   compare the extracted graph to the reviewed expected graph.
4. Execute the job in process inside the isolated container and collect events,
   step completion, materializations, exceptions and asset-check verdicts.
5. Check every declared intermediate/final artifact for existence, size, format,
   required CSV columns/row counts or finite JSON/required keys.
6. Compare declared outputs to private expected JSON or CSV files.

`dagster_executable` requires successful execution and task coverage. A failed
nonblocking asset check also fails execution qualification. `output_contract_valid`
and `behaviorally_correct` report their own binary outcomes. `complete_success` is
1 only when all six stages pass. A graph can be wrong even if its execution and
outputs pass; complete success remains 0 in that case. Graph differences do not
prevent collecting execution diagnostics.

Each stage uses `pass`, `fail`, `not_reached`, `timeout`, or `infra_error`.
Unreached stages never pass. Infrastructure errors produce null scores. Each
attempt's report directory contains `result.json`, static/runtime logs, Dagster
evidence and declared artifacts. Method/model/track/repetition/attempt metadata is
operator-supplied, and initial versus repaired attempts must be retained separately.

## Graph and output checks

Graph checking currently requires exact equality of actual and expected asset keys
or top-level op names and directed edges. The structure fraction counts matched
nodes and edges over expected plus unexpected nodes and edges, with no custom
weights. Semantic RQ1 task matching, split/merge mappings and nested-op normalization
need separate review. This graph metric alone does not establish task semantics.

JSON oracles require exact keys and types, preserve array order and reject
nonfinite values. Numeric equality uses:

```text
abs(actual - expected) <= atol + rtol * abs(expected)
```

CSV oracles preserve column and row order and use the same tolerance for numeric
cells. Text is compared exactly. Numeric-looking identifiers require a typed
comparator extension when lexical identity matters. Oracle values must come from
independently qualified benchmark behavior. Do not expose private assertions to
generation or automated repair. Declare all mandatory intermediate/final checks.

## Current scope

The evaluator qualifies local Dagster execution; it does not test distributed
execution or scheduler parallelism. Dedicated semantic model/plot/clustering
oracles, typed CSV schemas, file-read tracing, upstream perturbation tests and
benchmark-specific task mappings remain extensions. Wall-clock times are captured;
peak resource usage, generation token counts and monetary costs are not yet
instrumented. Container evidence assumes ordinary generated code rather than a
hostile attempt to forge evaluator evidence.

The six-stage implementation is independent of a particular application. Any
application's export limitations remain a property of that experimental method.

Dagster API references: [Definitions](https://dagster.io/docs/api/dagster/definitions)
and [execution](https://dagster.io/docs/api/dagster/execution). The adapter is tested
against the locked version rather than assuming the online latest API is identical.
