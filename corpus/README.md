# InLumen benchmark improvement: batches 01-21

Date: 30 October 2026. Status: all one hundred numbered upstream pipelines are represented in twenty-one batches, with Python reference qualification passing. Independent specification review and Dagster runtime qualification remain pending. These are behavioral revisions of upstream cases, not claims that the upstream scripts already perform the revised work.

## Recommendation

Improve the corpus in batches of approximately 3-5 cases, selected by actual computational behavior. For each batch, agree on a clear task specification, write its task/dependency reference JSON, align the executable reference with that specification, and qualify the outputs before expanding. More detailed text alone would preserve the current description/code mismatches.

Use diversity in operation, input structure, temporal assumptions, task count, and required artifact exchange. Changing domain names or techniques in otherwise identical templates will not establish diversity. Keep the first batch small enough to review every requirement.

## First batch

| Upstream ID | Problem motivating selection | Revised behavior | Reference tasks |
| --- | --- | --- | --- |
| 042 sports validation/recovery | Generic regression does not implement a defined recovery policy | Normalize roster fields, reject invalid identities/games, recover missing measures by position, and produce a computed audit report | 4 |
| 058 transportation geospatial | No explicit spatial computation; generic model targets destination longitude | Validate coordinates, compute haversine distances and passenger-km, aggregate by route, and report ranked routes | 4 |
| 008 energy forecasting | Ambiguous target fallback, random split, and preprocessing before split | Join previous-day weather, create lagged predictors, use chronological partitions, fit train-only scaling and Ridge, and evaluate actual test predictions | 7 |

This introduces three behavior families: group-wise recovery, spatial ETL, and temporal multi-source supervised regression. These initial graphs are linear. They predate the topology-diversity policy introduced with batch 03 and are queued for genuine behavioral restructuring rather than cosmetic relabeling.

Sports and transportation inputs include documented deterministic defects so the required rejection/recovery behavior actually occurs. The energy input is copied without semantic modification. Details and hashes appear in each `provenance.json`.

The energy variant uses observed lagged consumption and preceding-day weather, with a fixed model and rolling test prediction. It makes no claim about recursive forecasting, unknown future covariates, or production forecast accuracy. The original generic ML stages were deliberately removed from the two ETL tasks rather than retained as unrelated boilerplate.

## Second batch

| Upstream ID | Problem motivating selection | Revised behavior | Reference tasks |
| --- | --- | --- | --- |
| 003 credit risk | Sixteen broad stages mix compliance, fairness, explainability, and incompatible model choices | Reconcile three sources, aggregate account history, perform a stratified split, fit fixed train-only logistic regression, and evaluate held-out predictions | 5 |
| 004 customer churn | A large modeling playbook hides an independently useful relational task | Aggregate transaction behavior, integrate all customers, summarize segment churn cohorts, and report global measures | 4 |
| 005 demand forecasting | Many unspecified forecasting methods obscure the actionable inventory calculation | Build a zero-filled trailing 90-day demand grid and compute deterministic lead-time/service-level/MOQ reorder quantities | 3 |
| 006 e-commerce recommendation | The upstream implementation clusters demographics rather than creating recommendations from orders | Aggregate customer-product interactions and rank unseen, in-stock products using an explicit affinity/popularity/rating formula | 3 |
| 014 sports clustering | Assignments and profiles are not saved, and arbitrary K-means labels prevent exact comparison | Standardize ten declared features, fit fixed K-means, canonicalize labels by centroids, and publish assignments/profiles | 3 |

Batch 02 adds five distinct behavior families: multi-source classification, relational cohort aggregation, temporal inventory planning, deterministic recommendation/ranking, and unsupervised clustering. It deliberately includes both learned and non-learned workflows, avoiding another set of generic train/test prediction templates.

All source key relationships were audited before revision: there are no orphan applications, customers, products, SKUs, or suppliers in the selected fixtures. JSON and XLSX sources are converted deterministically to CSV for a uniform, portable generator-input contract; each `provenance.json` records the source filename, conversion, upstream commit, and resulting hash. The data are complete enough to execute every revised computation without external downloads.

## Third batch and topology policy

Batch 03 is the first topology-controlled batch. It contains exactly one linear pipeline and four structurally distinct non-linear pipelines:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 001 stock/market analytics | `linear_to_fan_in` | Stock and index validation run independently, converge for a date join, then continue through analysis/report | 5 |
| 007 employee attrition | `parallel` | Workforce, engagement, and performance analyses form three independent two-task components | 6 |
| 009 healthcare readmission | `fan_in_fan_out` | Four source summaries converge, three analyses reuse the integrated table, and their results reconverge | 9 |
| 010 HR salary/workforce | `linear_to_fan_out` | Integration and common feature engineering precede three independent analytical leaves | 5 |
| 054 student performance | `linear` | One source and one model objective require a six-stage chain | 6 |

For every new five-case batch, the default policy is at most one linear case and at least four distinct topology classes. Task counts must follow meaningful observable operations rather than a numerical quota. A topology may be assigned only when the computation and artifact flow require it; adding empty split/join nodes merely to satisfy diversity is invalid.

`corpus-diversity.json` inventories task counts and topology by batch. It marks batches 01 and 02 as pre-policy migration work rather than pretending their existing chains are diverse.

## Fourth batch

Batch 04 also satisfies the topology policy and adds qualified pure fan-in and fan-out cases:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 011 HR workforce | `fan_out` | One validated workforce table directly feeds three independent descriptive leaves | 4 |
| 012 insurance claims | `fan_in` | Three independent claims analyses converge only for portfolio reporting | 4 |
| 013 predictive maintenance | `fan_in_fan_out` | Past-only temporal/baseline features converge, then dual-horizon models and risk analysis fan out and reconverge | 8 |
| 015 sports clustering/prediction | `parallel` | Clustering and All-Star classification form two disconnected three-task components | 6 |
| 055 transportation delay | `linear` | A single delay-regression objective uses a six-stage chain | 6 |

The maintenance case deliberately increases task and dependency complexity: eight tasks, eleven artifact-backed edges, two split nodes, and two join nodes. The insurance fixture's supplied `report_delay_days` is treated as authoritative because its independently generated calendar dates do not encode that duration; this source limitation is explicit in the prompt rather than silently repaired.

## Fifth batch

Batch 05 satisfies the same policy with task counts from four to seven:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 002 treatment analytics | `linear` | Sufficient statistics and context are carried forward through one five-stage chain | 5 |
| 019 sports player analysis | `fan_out` | One prepared player table feeds prediction, availability, and compensation leaves | 4 |
| 023 sports market value/style | `parallel` | Regression and clustering are disconnected three-task components | 6 |
| 063 transportation clustering | `linear_to_fan_out` | Validation/preparation/clustering precede three independent post-cluster consumers | 6 |
| 079 transportation economics | `fan_in_fan_out` | Revenue/cost feature branches converge, then modeling/route analysis fan out and reconverge | 7 |

Topology validation changed the design during qualification: the experimental case initially reread earlier row data and the transportation clustering leaves initially reread pre-cluster features. Those dependencies would have created hidden joins. Both cases now carry the necessary information forward in immediate-parent artifacts, so their declared structures are real rather than cosmetic.

## Sixth batch

Batch 06 extends the task-count range within a batch to four through nine:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 017 player-style clustering | `fan_in_fan_out` | Shooting/playmaking branches converge, then three cluster views fan out and reconverge | 9 |
| 020 player analytics | `parallel` | Prediction, position statistics, and team chart data are three disconnected two-task components | 6 |
| 030 player ranking | `linear` | Validation, features, ranking, position selection, and reporting form one chain | 5 |
| 084 route service scoring | `linear_to_fan_in` | Reliability and satisfaction branches converge before scoring, ranking, and reporting | 5 |
| 099 transportation recovery | `fan_out` | One recovery task feeds independent route, vehicle, and weather summaries | 4 |

The recovery fixture includes five documented deterministic defects—one missing value in each of three numeric fields and one blank value in each of two categorical fields—so groupwise recovery and audit counts are directly testable.

## Seventh batch

Batch 07 contains five topology classes and task counts from four through nine:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 018 player clustering | `linear_to_fan_out` | Shared validation/features/clustering feed profiles, team mix, and PCA plot data | 6 |
| 021 All-Star diagnostics | `fan_in_fan_out` | Performance/shooting features converge, then three diagnostic branches reconverge | 9 |
| 031 sports summaries | `fan_in` | Team, position, and experience summaries converge only at reporting | 4 |
| 057 route performance | `linear` | Validation, features, aggregation, ranking, and report form one chain | 5 |
| 085 spatial/service analysis | `parallel` | Geospatial and service-quality analyses form two disconnected three-task components | 6 |

## Eighth batch

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 022 All-Star availability model | `fan_in_fan_out` | Performance/availability features converge, then metrics/team diagnostics reconverge | 8 |
| 032 shooting ranking | `linear` | Validation, scoring, ranking, selection, and reporting form one chain | 5 |
| 038 sports summaries | `fan_in` | Team, position, and age summaries converge only for reporting | 4 |
| 056 trip operations | `fan_out` | Prepared trips feed route, vehicle, and weather operational views | 4 |
| 087 route service analysis | `linear_to_fan_out` | Shared validation/features/route metrics feed three independent leaves | 6 |

## Ninth batch

Batch 09 contains exactly one linear case, five topology classes, and task counts from four through six:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 024 market value/All-Star modeling | `parallel` | Regression and classification form two disconnected three-task components | 6 |
| 033 shooting/value ranking | `linear` | Validation, scoring, ranking, selection, and reporting form one chain | 5 |
| 039 sports summaries | `fan_in` | Team, position, and age summaries converge only for reporting | 4 |
| 059 trip operations | `fan_out` | One prepared trip table feeds route, vehicle, and weather views | 4 |
| 088 route service analysis | `linear_to_fan_out` | Validation/features/route metrics precede three independent analytical leaves | 6 |

The parallel case adds a dual supervised-learning workload rather than another single-model chain. Its components deliberately use different split policies and metrics while remaining artifact-independent. The other cases retain only branches justified by independent summaries or consumers.

## Tenth batch

Batch 10 deliberately restores a wider four-to-nine task range while retaining exactly one linear case and five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 016 player-style clustering | `fan_in_fan_out` | Performance/context features converge; three cluster analyses fan out and reconverge | 9 |
| 034 shooting/value ranking | `linear` | Validation, scoring, ranking, selection, and reporting form one chain | 5 |
| 060 trip operations | `fan_out` | One prepared trip table feeds route, vehicle, and weather summaries | 4 |
| 076 delay/geospatial analysis | `parallel` | Delay classification and geographic route analysis are disconnected components | 6 |
| 086 geographic/service ranking | `linear_to_fan_in` | Geographic and service roots converge before scoring, ranking, and reporting | 6 |

The nine-task clustering case has two genuine joins and two genuine splits, with every edge bound to a material artifact. The transportation parallel case combines learned and deterministic spatial workloads without inventing a dependency between them. The geographic/service case uses both independent route summaries in its declared score, making its convergence behavior observable.

## Eleventh batch

Batch 11 retains a four-to-nine task range, exactly one linear case, and five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 025 shared-feature dual modeling | `fan_in_fan_out` | Performance/availability features converge, dual models fan out, and metrics reconverge | 9 |
| 035 shooting/value ranking | `linear` | Validation, scoring, ranking, selection, and reporting form one chain | 5 |
| 061 trip operations | `fan_out` | One prepared trip table feeds route, vehicle, and weather summaries | 4 |
| 068 delay/cancellation modeling | `parallel` | Classification and risk regression form disconnected three-task components | 6 |
| 081 route economics/service | `linear_to_fan_out` | Shared validation/features/route aggregation feed three independent analyses | 6 |

The large sports graph carries shared features into two different supervised objectives and explicitly reconverges their evaluations. The transportation parallel graph uses two targets but does not introduce an artificial cross-model dependency. The economics/service fan-out exposes profitability, service, and trade-off consumers from one reproducible route-level artifact.

## Twelfth batch

Batch 12 again spans four through nine tasks, with exactly one linear case and five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 027 shared-context dual modeling | `fan_in_fan_out` | Performance/context branches converge, dual models fan out, and metrics reconverge | 9 |
| 036 shooting/value ranking | `linear` | Validation, scoring, ranking, selection, and reporting form one chain | 5 |
| 048 team/region analysis | `parallel` | Performance and home-location analyses form disconnected three-task components | 6 |
| 066 trip geography | `fan_out` | One geographic trip artifact feeds route, vehicle, and departure-period views | 4 |
| 082 economics/service route ranking | `linear_to_fan_in` | Independent economics/service summaries converge before scoring, ranking, and reporting | 6 |

This batch adds a parallel descriptive/geospatial case rather than another pair of models. Its two components use different source fields and produce independently useful reports. The geospatial fan-out makes coordinate validation and haversine transformation shared observable work, while the economics/service case requires both roots in its composite score.

## Thirteenth batch

Batch 13 spans four through nine tasks, contains exactly one linear case, and adds another pure fan-in case:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 028 valuation diagnostics | `fan_in_fan_out` | Performance/context features converge; model/team/position branches fan out and reconverge | 9 |
| 037 position performance | `linear` | Validation, features, aggregation, ranking, and reporting form one chain | 5 |
| 067 trip operations | `fan_out` | One prepared trip table feeds route, weekday, and weather summaries | 4 |
| 083 trip economics | `linear_to_fan_out` | Shared trip economics feed route ranking, vehicle economics, and weather economics | 6 |
| 089 service portfolio | `fan_in` | Independent route, vehicle, and weather summaries converge only at reporting | 4 |

The valuation graph uses one supervised objective plus two descriptive branches, rather than duplicating a dual-model pattern. The economics graph carries the trip-level economics artifact into the vehicle and weather leaves while only the route branch continues through route aggregation and ranking. This preserves a real split instead of claiming that route aggregates contain discarded vehicle/weather dimensions.

## Fourteenth batch

Batch 14 spans four through nine tasks, contains exactly one linear case, and increases linear-to-fan-in representation:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 026 shared-feature dual modeling | `fan_in_fan_out` | Performance/availability features converge, dual models fan out, and metrics reconverge | 9 |
| 043 team performance/chart data | `linear` | Preparation, aggregation, ranking, chart preparation, and reporting form one chain | 5 |
| 062 trip operations | `fan_out` | One prepared trip artifact feeds route, departure-period, and weather summaries | 4 |
| 071 delay/service analysis | `parallel` | Delay classification and route service analysis are disconnected components | 6 |
| 080 revenue/cost economics | `linear_to_fan_in` | Revenue and cost feature roots converge before aggregation, ranking, and reporting | 6 |

The parallel case combines a learned workflow with a deterministic service workflow rather than duplicating two models. The revenue/cost case makes its join observable through trip-level profit and margin, and all route-level outputs descend from that integrated artifact.

## Fifteenth batch

Batch 15 expands the within-batch range to four through ten tasks while retaining exactly one linear case and five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 029 valuation multiview | `fan_in_fan_out` | Three feature branches converge; model/team/position branches fan out and reconverge | 10 |
| 044 team performance/chart data | `linear` | Preparation, aggregation, ranking, chart preparation, and reporting form one chain | 5 |
| 064 trip operations | `fan_out` | One prepared trip artifact feeds route, weekday, and weather summaries | 4 |
| 072 delay/service analysis | `parallel` | Delay classification and route service analysis are disconnected components | 6 |
| 095 trip geography | `linear_to_fan_out` | Shared validation/geographic features feed route ranking, vehicle, and period views | 6 |

The ten-task valuation case raises the corpus task-count maximum from nine to ten through a third meaningful feature branch, not through empty orchestration. Its downstream model evaluation and two group diagnostics reconverge only for count reconciliation and reporting. The geospatial case preserves trip-level dimensions for vehicle and period leaves while only the route branch performs route aggregation and ranking.

## Sixteenth batch

Batch 16 retains a four-to-ten task range, exactly one linear case, and five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 040 sports cohort analysis | `fan_in_fan_out` | Three feature branches converge; four cohort summaries fan out and reconverge | 10 |
| 047 position feature ranking | `linear` | Validation, features, aggregation, ranking, and reporting form one chain | 5 |
| 065 trip operations | `fan_out` | One prepared trip artifact feeds route, vehicle, and departure-period views | 4 |
| 069 delay/risk modeling | `parallel` | Classification and regression form disconnected three-task components | 6 |
| 090 service portfolio | `fan_in` | Independent route, vehicle, and weather summaries converge only at reporting | 4 |

The ten-task case is fully descriptive: it demonstrates that higher task counts need not be tied to model training. Its four downstream cohort artifacts each retain independently meaningful statistics and reconcile to the same player population. The pure fan-in case increases representation of convergent reporting structures.

## Seventeenth batch

Batch 17 spans four through ten tasks and contains exactly one linear case across five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 077 delay-model diagnostics | `fan_in_fan_out` | Operational/context features converge; model and three diagnostics fan out and reconverge | 10 |
| 045 audited player recovery | `linear` | Audit, numeric recovery, categorical recovery, aggregation, and reporting form one chain | 5 |
| 070 delay/risk modeling | `parallel` | Classification and regression form disconnected three-task components | 6 |
| 091 trip operations | `fan_out` | One prepared trip artifact feeds route, vehicle, and departure-period views | 4 |
| 096 operational portfolio | `fan_in` | Independent route, vehicle, and weather summaries converge only at reporting | 4 |

The recovery input deliberately contains four documented deterministic defects: one missing points value, one missing salary, one blank team, and one blank position. Its provenance records the exact row indices and columns. Qualification verifies all four recovery flags, zero remaining missing values, and complete row reconciliation. This makes recovery observable rather than retaining an unused recovery label on complete source data.

## Eighteenth batch

Batch 18 spans four through ten tasks, contains exactly one linear case, and adds a recovery-driven linear-to-fan-out case:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 078 delay-model diagnostics | `fan_in_fan_out` | Operational/context features converge; model and diagnostics fan out and reconverge | 10 |
| 046 audited player recovery | `linear` | Audit, numeric recovery, categorical recovery, aggregation, and reporting form one chain | 5 |
| 049 recovery cohort views | `linear_to_fan_out` | A three-task recovery stem feeds team, position, and age summaries | 6 |
| 073 delay/risk modeling | `parallel` | Classification and regression form disconnected three-task components | 6 |
| 092 trip operations | `fan_out` | One prepared trip artifact feeds route, vehicle, and departure-period views | 4 |

Both recovery inputs contain the same four defect types at documented row indices, but their graphs test different composition behavior. The linear case produces audit and recovery reports; the fan-out case carries recovery flags into three independent cohort summaries. Qualification confirms zero remaining missing values and complete row reconciliation for both.

## Nineteenth batch

Batch 19 spans four through ten tasks and contains exactly one linear case across five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 041 sports cohort analysis | `fan_in_fan_out` | Three feature branches converge; four cohort summaries fan out and reconverge | 10 |
| 051 position feature ranking | `linear` | Validation, features, aggregation, ranking, and reporting form one chain | 5 |
| 075 delay/risk modeling | `parallel` | Classification and regression form disconnected three-task components | 6 |
| 093 trip operations | `fan_out` | One prepared trip artifact feeds route, vehicle, and departure-period views | 4 |
| 097 operational portfolio | `fan_in` | Independent route, vehicle, and weather summaries converge only at reporting | 4 |

Seven unused upstream cases remain after this batch. One further full five-case batch can satisfy the standard policy. The final two cases will require either a documented partial-batch exception or inclusion with genuine migrations of three pre-policy cases; they should not be padded with duplicate cases or artificial nodes.

## Twentieth batch

Batch 20 expands the range to four through eleven tasks, contains exactly one linear case, and uses five topology classes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 074 recovered delay diagnostics | `fan_in_fan_out` | Recovery precedes convergent features; model and diagnostics fan out and reconverge | 11 |
| 052 position feature ranking | `linear` | Validation, features, aggregation, ranking, and reporting form one chain | 5 |
| 050 recovery cohort views | `linear_to_fan_out` | A three-task recovery stem feeds team, position, and age summaries | 6 |
| 094 trip operations | `fan_out` | One prepared trip artifact feeds route, vehicle, and departure-period views | 4 |
| 098 operational portfolio | `fan_in` | Independent route, vehicle, and weather summaries converge only at reporting | 4 |

The eleven-task prediction case raises the corpus maximum through an explicit audit/recovery stage. Its input contains one missing distance, fare, vehicle, and weather value at documented row indices. Recovery audit data and all diagnostic branches are consumed by the final report. Qualification verifies complete recovery, all 731 trips, and the fixed held-out split.

Only upstream cases 053 and 100 remain unused. A final five-case batch cannot be formed from unused cases alone. The defensible choices are a two-case final partial batch or a five-case migration batch containing those two plus three genuinely redesigned pre-policy cases.

## Final partial batch

Batch 21 contains the final two unused upstream sources. It is explicitly marked as a partial final batch rather than padded with duplicates or artificial nodes:

| Upstream ID | Topology | Structural reason | Tasks |
| --- | --- | --- | ---: |
| 053 recovery cohort views | `linear_to_fan_out` | A three-task recovery stem feeds team, position, and age summaries | 6 |
| 100 route performance/chart data | `linear` | Preparation, aggregation, ranking, chart preparation, and reporting form one chain | 5 |

The batch preserves the one-linear-case limit and uses two distinct justified topologies. Case 053 contains one missing points value, salary, team, and position at documented row indices; qualification verifies complete recovery and reconciliation of all 584 players. Case 100 reconciles all 613 trips through route ranking and chart-data preparation. No numbered upstream source remains unused.

## Files per pipeline

```text
pipelines/<upstream-id>/
  description.md        Authoritative task requirements
  prompt.txt            Standardized UTF-8 task prompt for automated generation
  inputs/               Allowed input CSV files
  task_graph.json       Evaluator-owned reference for tasks/dependencies
  reference.py          Revised executable Python reference
  requirements.txt      Exact direct dependency pins used for reference checks
  provenance.json       Upstream revision, input changes/hashes and revision rationale
```

`description.md` specifies the purpose, exact input columns, transformations, invalid/missing-value policies, parameters, output artifacts, dependency requirements, numerical tolerances, and boundary conditions. It contains neither reference code nor expected numerical answers. It specifies mandatory behavior/checkpoints rather than insisting on an exact number of Dagster nodes.

Every case has `prompt.txt`, rendered from `description.md` using the versioned
`servicecraft.task-prompt@2` template. Read
`prompt.txt` once as the task message for direct generation, InLumen, Pi and Aider.
The seven standard sections cover objective, available input files/columns,
processing behavior, dependency/topology requirements, mandatory output artifacts,
execution/numerical rules and deliverable. All task-specific source paragraphs and
output annotations are preserved. Input inventories come from public fixture
headers; neither reference graphs nor private answers inform the renderer.
Do not concatenate both description and prompt into the model context.
Keep common runtime/submission instructions separate, versioned and identical
across methods. This task-text standardization does not yet define that shared
runtime wrapper or implement a generation driver. Prompt availability does not
change pending author semantic-review status.

After deliberately editing a description, regenerate and verify the prompt copies:

```sh
python3 corpus/tools/sync_prompts.py \
  --evaluation-corpus evaluation/corpus
python3 corpus/tools/sync_prompts.py \
  --evaluation-corpus evaluation/corpus --check
```

`prompt-manifest.json` records the template version, renderer hash and each case's
source-description, input-inventory and rendered-prompt hashes. The synchronizer
also publishes the same `prompt.txt` into each standalone
evaluation corpus case. It reads no reference implementation or private expected
answer. The exporter includes `prompt.txt` and retains `description.md` for
compatibility; it rejects stale prompt text. Record the exact prompt SHA-256,
shared wrapper version and model configuration in each generation run.

The direct dependency pins and recorded installed versions support reproducibility, but are not a transitive hash lock or an isolated fresh-install certification. A container/environment lock and actual Dagster packaging are later qualification steps.

## JSON design for RQ1

Each `task_graph.json` follows `task-graph.schema.json` and records:

- Pipeline identity, domain, behavior family, revision, and review status.
- Input artifacts and their required columns.
- Stable reference task IDs, task names, operation types, semantic requirements, required parameters, consumed artifacts, and produced artifacts.
- Artifact files, formats, and required columns.
- Directed dependencies, including the specific artifacts exchanged.
- A scoring policy allowing valid split/merged implementations and requiring real data bindings for data edges.
- Reference entry points for qualification, kept away from the generation routes.

For example, sports recovery depends on eligible rows and the validation audit; a report depends on recovered data and the recovery audit. Energy training consumes the train/test partitions produced by splitting. These are data requirements, not just neighboring positions in a list.

Task-graph schema v2 supports `linear`, `parallel`, `fan_in`, `fan_out`, `fan_in_fan_out`, `linear_to_fan_in`, and `linear_to_fan_out`. The validator derives roots, sinks, joins, splits, weak components, and acyclicity from artifact-backed edges and rejects a topology label that does not match the graph. It still does not model conditional execution, retries, control-only edges, loops, streaming, or service catalogs; those require a later versioned extension.

### What JSON can and cannot automate

JSON enables deterministic checks of task coverage, dependency constraints, required parameters, artifact bindings, and full task/dependency correctness **after candidate tasks have been mapped to the reference requirements**. Candidate Dagster node names need not equal the reference IDs.

It does not, by itself, solve semantic matching. Calling a node `recover` does not establish that its definition specifies the correct recovery strategy. The mapping must inspect candidate task definitions/code using a reviewed normalization procedure. Valid one-to-many or many-to-one task mappings must preserve the requirements and observable artifacts. Unknown semantics must remain unassessed, not silently pass. Implementation behavior is checked separately for RQ2/RQ3.

For the next scoring step:

1. Extract a normalized candidate task/dependency representation from each route's actual output; do not use the reference graph to fill missing candidate structure.
2. Map candidate tasks to reference requirements and inspect the declared operations/parameters, retaining uncertainty.
3. Check mandatory logical coverage, parameter constraints, required precedence, and artifact binding preservation under that mapping. Allow valid split/merged task decompositions.
4. Report design assessability, complete correctness over all attempts, and diagnostic task/dependency errors. Keep unknown or invalid candidates in the primary denominator.

The included `validate_specs.py` validates reference specification shape, unique/resolvable IDs, single producers, dependency/artifact consistency, acyclicity, declared topology structure, input hashes, and output-file coverage in descriptions. It is not yet an extractor, candidate scorer, or a proof that all semantic prose matches code.

## Avoid leaking RQ1 answers

For natural-language RQ1/RQ3 runs, expose `prompt.txt`, its source-description compatibility file `description.md`, and `inputs/` to all methods. Send only `prompt.txt` as the task message. Do not attach the entire pipeline folder or give a generator file-system access to evaluator files. Reference JSON may be released with the final research artifact later, but it must not be available during the scored generation experiment.

For fixed-graph RQ2, provide those inputs plus the sanitized `provided_graph.json` produced by the export tool. Reference implementations, provenance/change hints, qualification fixtures, and expected outputs are excluded in both tracks. The fixed-graph export includes the reviewed design/contract information intentionally.

The allowlist exporter refuses to overwrite an existing destination. Example commands, from the project root:

```bash
python3 corpus/tools/export_inputs.py \
  042_sports_validation_recovery /tmp/inlumen-sports-natural \
  --track natural_language

python3 corpus/tools/export_inputs.py \
  008_energy_forecasting /tmp/inlumen-energy-fixed \
  --track fixed_graph
```

The future experiment driver should mount only the exported bundle. A file convention alone does not create an access-control boundary. The exporter does not assign an experimental execution policy or spend LLM calls.

## Qualification performed

Run the references with Python, independently compute expected behavior, and check emitted intermediate/final artifacts. The reusable qualification script covers:

- All three revised visible input fixtures, required output files, CSV columns and finite JSON.
- Sports group/global/zero imputation and rejection-priority behavior.
- Geographic zero-distance and antipodal cases, invalid coordinates, ranking ties, and an empty valid partition.
- Shuffled temporal inputs, previous-day weather, chronological partitions, train-only scaling, and held-out predictions checked against an independent NumPy closed-form Ridge solution.
- Rejection of missing energy hours and duplicate weather dates.
- Rejection of a missing required artifact dependency in the JSON.
- Export allowlists for all three cases in both experiment tracks.

See the twenty-one qualification reports in this directory. Batch 01 and batch 02 each have 11 check groups. Batches 03–20 each have 12: five visible-reference/invariant/topology checks, five invalid-input checks, a wrong-topology-label check across all five graphs, and a two-track export check. The final two-case Batch 21 has six applicable groups: two visible-reference/invariant/topology checks, two invalid-input checks, one wrong-topology-label check, and one two-track export check.

Re-run from the project root using Python with the recorded NumPy/pandas/scikit-learn/SciPy versions and `jsonschema==4.24.0`:

```bash
python3 corpus/tools/validate_specs.py
python3 corpus/tools/qualify_batch01.py
python3 corpus/tools/qualify_batch02.py
python3 corpus/tools/qualify_batch03.py
python3 corpus/tools/qualify_batch04.py
python3 corpus/tools/qualify_batch05.py
python3 corpus/tools/qualify_batch06.py
python3 corpus/tools/qualify_batch07.py
python3 corpus/tools/qualify_batch08.py
python3 corpus/tools/qualify_batch09.py
python3 corpus/tools/qualify_batch10.py
python3 corpus/tools/qualify_batch11.py
python3 corpus/tools/qualify_batch12.py
python3 corpus/tools/qualify_batch13.py
python3 corpus/tools/qualify_batch14.py
python3 corpus/tools/qualify_batch15.py
python3 corpus/tools/qualify_batch16.py
python3 corpus/tools/qualify_batch17.py
python3 corpus/tools/qualify_batch18.py
python3 corpus/tools/qualify_batch19.py
python3 corpus/tools/qualify_batch20.py
python3 corpus/tools/qualify_batch21.py
python3 corpus/tools/summarize_diversity.py
```

Regenerate the copied inputs/specifications/descriptions only when deliberately reapplying this pilot definition:

```bash
python3 corpus/tools/prepare_batch01.py
python3 corpus/tools/prepare_batch02.py
python3 corpus/tools/prepare_batch03.py
python3 corpus/tools/prepare_batch04.py
python3 corpus/tools/prepare_batch05.py
python3 corpus/tools/prepare_batch06.py
python3 corpus/tools/prepare_batch07.py
python3 corpus/tools/prepare_batch08.py
python3 corpus/tools/prepare_batch09.py
python3 corpus/tools/prepare_batch10.py
python3 corpus/tools/prepare_batch11.py
python3 corpus/tools/prepare_batch12.py
python3 corpus/tools/prepare_batch13.py
python3 corpus/tools/prepare_batch14.py
python3 corpus/tools/prepare_batch15.py
python3 corpus/tools/prepare_batch16.py
python3 corpus/tools/prepare_batch17.py
python3 corpus/tools/prepare_batch18.py
python3 corpus/tools/prepare_batch19.py
python3 corpus/tools/prepare_batch20.py
python3 corpus/tools/prepare_batch21.py
```

That command rewrites this batch's fixture/specification files. It leaves the upstream checkout and references unchanged. Review source revisions and re-run qualification afterward. The qualification report is refreshed only after all checks pass.

No Dagster package was installed or run for these batches. The references are trusted behavioral oracles, not Dagster projects, and their plain-Python qualification must not be reported as Dagster validity. RQ1 semantic extraction/scoring and InLumen/direct generation have not yet been run.

## Batch gates and next selection

Treat these cases as development/pilot cases if they are used to tune descriptions, prompts, scorers, or generation behavior. Keep final evaluation cases or task families separate under a declared split policy.

Before scaling each batch:

1. Review whether every requirement in the prompt has the same meaning in the JSON and reference. Check that no scored condition is absent from the prompt.
2. Review whether the revised computation is useful and sufficiently different from existing cases.
3. Require graph/artifact validation and independent behavioral checks to pass.
4. Add and qualify reference Dagster adapters under the experiment's pinned environment.
5. Confirm both generator input exports are equivalent within each track and exclude evaluator material.
6. Freeze the case revision and record reviewer/qualification status.

All numbered upstream sources are now represented. Batches 03–20 comply with the standard five-case policy; Batch 21 is a documented final two-case exception that preserves the one-linear limit and distinct-topology requirement. The next corpus work should focus on independent semantic review, declared train/development/test splitting, and Dagster runtime qualification rather than adding more source variants.

## Technical references

- [Haversine distance definition and angular units](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.haversine_distances.html).
- [Ridge least-squares objective and solver options](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html).
- [StandardScaler fitting and population variance](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).

These documentation pages were checked while authoring the pilot. Qualification records the actual installed version, scikit-learn 1.7.0; online stable documentation may describe a newer release.
