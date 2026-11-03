# ServiceCraft instructions for AI tools

## Purpose and layout

This is a standalone research benchmark and evaluator, not the InLumen application.
Read README.md first. `corpus/` contains 100 source cases, public fixtures,
descriptions/prompts, task graphs, references and provenance. `evaluation/` is the
installable Python project. `evaluation/corpus/` packages trusted Dagster controls,
scoring specifications, oracle contexts and expected outputs. These are operator
assets, not generated experimental submissions.

## Working directory and commands

From repository root, Python 3.11+:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e './evaluation[test,corpus]'
python -m pytest evaluation/tests -q
python -m unittest discover -s corpus/tools -p test_prompt_format.py -v
python corpus/tools/sync_prompts.py --evaluation-corpus evaluation/corpus --check
python corpus/tools/validate_specs.py
```

Build the Docker runtime with `docker build -t servicecraft-runtime:1.13.12
evaluation`. Build oracles with `docker build -f evaluation/Dockerfile.oracles
-t servicecraft-oracle:corpus-v1 evaluation`. The README includes a complete
small evaluation example. Run `evaluation/tools/qualify_*` scripts from
`evaluation/`, passing `../corpus` for the benchmark root where required.
Use new output directories. Never erase previous evidence to make a run pass.

## Corpus changes

- Preserve case IDs, input hashes, provenance and author-review status unless the
  requested change explicitly updates them with evidence. Never sign off as the author.
- Edit `description.md` as authoritative task prose. Publish prompts with
  `python corpus/tools/sync_prompts.py --evaluation-corpus evaluation/corpus`.
  Do not hand-edit generated prompt copies or manifests. The renderer is
  `corpus/tools/prompt_format.py`.
- Prompts must retain topology semantics, task behavior, numerical parameters,
  validation/recovery policies and observable outputs. Do not invent requirements
  to fill gaps or transcribe private answers into natural-language prompts.
- If changing semantics, align description, graph, reference, contracts and oracle,
  update provenance and requalify affected cases. Record unresolved ambiguities.
- Independent branches and joins must represent real computations and artifact
  exchange. Do not create empty assets or replay the whole reference per task.
- Exact node names/counts are not a substitute for semantic task correctness.
  Keep explicit physical/logical mappings and permit only reviewed equivalent
  decompositions.

## Evaluation changes

- Keep candidate/input directories separate from private specifications and oracles.
- Keep complete success binary. Preserve raw/scaled static diagnostics separately;
  do not introduce calibrated weights or a composite SAT score.
- Candidate failures are zeros. Setup/environment/evaluator failures are unavailable
  (null); retain them and follow declared rerun rules. Never drop hard cases.
- Freeze image versions, inputs, evaluator sources and profiles. Rebuilding an
  image requires new qualification, not retroactive historical approval.
- Run untrusted generated code and serialized models only through the isolated
  runtime/oracle paths. Do not load candidate pickle files in the host process.
- Tests should cover changed behavior. Use genuine Docker regression/affected-case
  runs for runtime, graph, mount, oracle or environment changes. Report inability
  to run them explicitly rather than claiming they passed.
- Historical qualification does not establish fresh-machine success, private
  held-out generalization, human semantic signoff or LLM-method performance.

## Benchmark generation is a different role

If implementing or operating a generation method, export an allowlisted task
workspace with `corpus/tools/export_inputs.py`. The model receives `prompt.txt`,
allowed inputs and the shared runtime/submission instructions. Only the fixed-graph
track receives sanitized `provided_graph.json`.

Do not expose this repository root, reference implementations, trusted controls,
private oracles, expected outputs or historical answer artifacts to the scored
model. Restrict filesystem access; a directory convention alone is insufficient.
Do not feed private final-evaluation results into repair. Development/public
feedback and private scoring must remain distinct. Capture all model calls,
repairs, tool use, latency, usage provenance and immutable submission checkpoints
when adding generation telemetry. Missing usage is not zero.

## Repository hygiene

Keep original per-case upstream provenance. No blanket upstream license has been
declared; see NOTICE.md. Do not add credentials, local environments, exported
workspaces or raw run directories to Git. Included `private/` files are benchmark
answer fixtures, not secret credentials. Check staged changes before committing.
Use `codex/` for new work branches unless the user specifies otherwise.
