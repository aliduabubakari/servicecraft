# Proposed method comparison and generation telemetry

Research/design note, 31 October 2026. This is a proposed protocol, not an
implemented generation driver or experimental result. The existing evaluator
qualifies submissions; generation telemetry still needs a separate driver.

## Recommended methods

Use four primary methods: direct one-shot generation, InLumen, Pi, and Aider.
Pi and Aider are the two proposed additions to the existing two-method plan.
Require every method to submit Dagster code under the same public runtime,
filesystem, dependency and artifact contracts.

| Method | Role | Proposed configuration |
| --- | --- | --- |
| Direct | Minimal prompting baseline | One generation request for a complete bundle; no automatic code repair |
| InLumen | Domain-specific structured construction | Freeze native design, node generation, validation, repair and Dagster export settings |
| Pi | General coding agent | Frozen release, file/shell tools, public validation command, bounded native loop |
| Aider | Coding and test/correction workflow | Frozen release, ordinary code mode, public lint/test command and bounded corrections |

These roles are methodological recommendations, not claims about relative
performance. Pi exposes JSON/RPC automation and structured lifecycle events.
Its current upstream repository redirects from badlogic/pi-mono to
earendil-works/pi. Record the exact commit and package lock rather than depending
on a mutable main branch. [Pi documentation](https://github.com/earendil-works/pi/tree/main/packages/coding-agent).

Aider provides a scriptable CLI and automatic lint/test correction. Use its CLI
as the initial integration; its Python scripting API explicitly lacks compatibility
guarantees. [Scripting](https://aider.chat/docs/scripting.html),
[testing](https://aider.chat/docs/usage/lint-test.html).

Use one designated backbone model per method/model cell. Disable automatic model
switching where possible. Pin any unavoidable editor, weak, summary or auxiliary
models, charge their usage to the method, and label that cell as a multi-model
configuration. Freeze Aider's edit format and automatic correction behavior after
development pilots. Do not use a different stronger model only for an agent.

The four-method comparison estimates whole-system differences. Direct generation
has fewer feedback opportunities, so an improvement cannot establish that
InLumen's architecture alone caused the difference. If that explanation matters,
add a small direct-with-bounded-public-feedback condition. It is an additional
baseline, not a component ablation or a replacement for the original direct arm.

## Two tracks and three research questions

Keep the natural-language and fixed-graph tracks separate:

- Natural-language track: same description, permitted fixtures/profiles and public
  runtime contract. No reference graph, control code, expected answers or private
  oracles. Score task/dependency correctness and end-to-end success.
- Fixed-graph track: same reviewed graph, explicit contracts, parameters and
  permitted fixtures. Score implementation validity without conditioning on
  success in the natural-language track.

Proposed research questions:

1. How accurately do the four methods represent required tasks and dependencies
   from natural-language requirements, across the selected backbone models?
2. Given a correct graph and explicit contracts, how reliably do the methods
   produce valid Dagster implementations with correct intermediate/final outputs?
3. How do the methods compare in end-to-end success and computational resources
   required under declared budgets, across the selected backbone models?

Do not reintroduce human-effort scoring or component-contribution claims.
Semantic RQ1 mapping remains separate from exact physical Dagster graph checks;
alternative valid decompositions require a frozen reviewed mapping procedure.

## Measurements

| Family | Measures | Interpretation |
| --- | --- | --- |
| Primary correctness | Complete success, success within every declared budget | Binary per episode; aggregate with explicit denominators |
| Design | Assessability, mandatory task/parameter coverage, dependency correctness, complete design correctness | RQ1, using reviewed semantic mapping |
| Validation ladder | Syntax, definition/graph, execution, artifact contracts, independent behavioral checks | Separate stage status and failure/not-reached reasons |
| Static quality | Existing raw and directly scaled lint, complexity, maintainability and structure measures | Diagnostic; no weighted SAT or combined quality score |
| Model resources | Input, output, cached input, cache write, reasoning when reported; model requests and retries | All generation work, including unsuccessful requests with reported usage |
| Time | Generation wall time, request latency, tool/validation time, queue/backoff, final evaluation time, total time | Monotonic clocks for durations; distinguish overlap |
| Monetary resources | Estimated API cost and billed cost where available; optional separately scoped infrastructure cost | Frozen rates, currency, date and billing categories |
| Work performed | Code-producing calls, node generations, repairs, edits, tool calls, validation executions, compactions | Separate counters rather than an ambiguous iteration total |
| Reliability | Budget exhaustion, unresolved clarification, API/system failures, candidate failure stage | Preserve every scheduled episode |

Keep per-artifact results, but average correctness at pipeline level for the
primary comparison. Otherwise cases with many artifacts dominate the result.
A fast failure is not an efficiency success. Report resource distributions over
all episodes and, separately, over successful episodes.

Cost per successful pipeline = total cost of all episodes / number of successes.
Time and tokens per success can use the same accounting. They are undefined
when there are no successes. Also report the success/cost tradeoff within each
backbone model; token counts alone are not a model-independent effort scale.

## What an iteration means

Use these explicit units across methods:

- Episode: one fresh case/method/model/track/repetition run, with fresh workspace.
- Model request: one actual provider request, including planning and summaries.
- Code-producing request: a request whose response generates or revises code.
- Node generation: one InLumen logical-node generation event, when applicable.
- Repair: a code revision explicitly triggered by observed failure feedback.
- Tool execution: one tool invocation, classified as read/edit/run/validate/etc.
- Submission checkpoint: an immutable, explicitly submitted full pipeline bundle.
- Infrastructure retry: an operational retry, distinct from code repair.

Pi turns are measurable but are not equivalent to InLumen node generations or
repairs. Retain native counters as secondary descriptions. Report total requests,
cost and wall time as common resource measures; use global limits as well as any
native per-node limits. A repair allowance per node grows with graph size.

For a genuine pre-repair pipeline score, capture a complete bundle before repair.
If InLumen must execute/repair early nodes before generating later nodes, its
first complete bundle already includes that work. Label it accurately. A separate
repair-disabled run is needed for a clean no-repair comparison when feasible.
Never call the first model response a first complete pipeline for every method.

## Tokens and cost

Persist raw provider usage plus normalized categories and a usage provenance
flag: provider-reported, locally estimated, or unavailable. Do not replace
unavailable usage with zero. Count repeated context each time it is sent.
Include design, generation, malformed-response recovery, repair, summarization,
compaction and any nested model work. Tokens of private offline evaluator work
are separate from construction resources.

Provider token categories may overlap. Reasoning can be a subset of output and
cached input can be a subset of input. Normalize to disjoint billable categories
before computing cost; retain the raw response for audit. Pi specifically documents
reasoning as included in output. Its message usage includes cache and cost fields.
[Pi message types](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/message-types.md).

Estimate API cost by summing each call's disjoint token categories multiplied by
their frozen category-specific per-token prices. Use exact resolved model IDs,
cache retention and provider tier where relevant. Native tool cost displays are
cross-checks, not an independently reconciled bill. Store estimated and billed
cost separately; preserve uncertainty for timed-out requests lacking final usage.

## Instrumentation feasibility and gaps

- InLumen: the inspected `inLUMEN/backend/design_sessions/llm.py` and
  `inlumen-codegen-service/app/llm.py` parse model content without persisting the
  provider usage object. Capture usage/latency/request IDs at both request
  boundaries, before JSON parsing. Audit other active model paths too. Existing
  generator retry/repair loops supply useful native events but a single returned
  attempts field is not a reliable total across nested loops.
- Direct: wrap the provider request and bundle extraction; preserve malformed
  outputs and request failures with their measured cost/time.
- Pi: use JSON/RPC events for turns, tool runs and lifecycle, and completed
  assistant messages for usage. Deduplicate messages repeated in end-of-turn/run
  events; do not sum cumulative streaming updates. Track compaction usage and
  automatic retries. [Event reference](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/json.md).
- Aider: preserve CLI and LLM histories, but instrument the underlying request
  boundary for authoritative usage and per-request timing. Its cost code falls
  back to local token estimates when provider usage is missing; mark that
  provenance. Count public test executions and feedback-driven revisions.
  [Options](https://aider.chat/docs/config/options.html),
  [usage implementation](https://github.com/Aider-AI/aider/blob/main/aider/coders/base_coder.py).
- Evaluator: currently provides stage evidence, binary outcomes, static metrics
  and evaluation elapsed time. It does not collect complete generation telemetry.
  Detailed per-stage wall times and resource counters would require further
  instrumentation if needed.

Log events with episode ID, event/request/parent IDs, method, resolved model,
stage/node, monotonic start/end, status, usage and provenance, feedback visibility,
checkpoint hash and cost/pricing version. Store UTC timestamps for audit.
Join these records to evaluation results by immutable checkpoint hash. Exclude
credentials and private expected answers from shared logs. Qualification runs are
not generation episodes and must not appear as paper observations.

## Fair feedback and budget policy

Give all iterative methods access to the same public diagnostics: syntax, imports,
Dagster load/runtime errors and public schema checks. They may use their own
tools within the frozen policy. Do not expose private expected values, assertions,
oracle code or hidden pass/fail to generation. The entire private corpus folder
must be inaccessible to coding agents, including through parent-directory reads.
Use isolated workspaces/home directories with no inherited skills, session memory
or unrelated project instructions. Run generated code in the pinned runtime;
control network/package installation so the agent cannot silently change it.

Choose time and monetary limits from development pilots; freeze identical limits
within each case/model/track comparison. Add a global request safety cap and
record actual usage. An in-flight request can overshoot a limit: define reservation
and cancellation rules and require observed budget compliance for budget success.
Different tokenizers make equal token limits across models an imperfect control.
Freeze reasoning settings and record unsupported settings instead of claiming
equivalence. Record cache policy and randomize run order to reduce order effects.

The final submitted checkpoint is the primary endpoint. If evaluating intermediate
checkpoints offline, predeclare their cadence and selection, never feed private
results back, and do not choose the best private-scoring candidate after the fact.
Time-to-first-correct is available only at the checkpoints actually assessed.
Timeout failures remain failures within budget, with time-to-success censored;
infrastructure-unavailable outcomes follow a separate predeclared rerun policy.

## Pilot and analysis

Start with 10 development cases spanning task counts and topologies, four methods,
two shared models and two repetitions in one track: 160 episodes. This is an
engineering pilot, not a power calculation. Check real usage capture, clean
workspace isolation, model compatibility, feedback limits and joinable evidence.
Freeze prompts/configuration afterward and distinguish pilot from main results.
Where possible keep implementation groups disjoint across development and test.

Full factorial scale is cases × methods × models × repetitions × tracks.
For 100 × 4 × 3 × 3 × 2 this is 7,200 generation episodes, excluding controls,
API retries and internal calls. Pilot costs determine whether both full tracks
are affordable; reduce declared scope before observing main outcomes if needed.

Compare paired case/model results, show uncertainty and per-model performance,
and account for repeated cases and shared reference implementations in inference.
The corpus has 69 exact code-fingerprint groups; that does not establish 69
independent semantic families. Define reviewed grouping before final inference.
Task count/topology effects are useful secondary analyses, with sparse strata
reported descriptively. Retain raw static metrics without a weighted aggregate.

Immediate next implementation: a method-neutral generation driver, four method
adapters, append-only request/tool/checkpoint telemetry, budget enforcement and
public-only validation. Keep independent scoring in the standalone evaluator.
