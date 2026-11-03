# Parallel player prediction, position statistics, and team chart data

Build three disconnected two-task components. Prediction prepares thirteen ordered predictors and all_star, then fits/evaluates a 75/25 stratified seed-42 StandardScaler+LogisticRegression pipeline with threshold 0.5 and five held-out metrics. Statistics prepares position aggregates then reports position/player counts and the highest all-star-rate position. Chart-data component prepares team counts, all-stars, mean points/salary then reports team/player/all-star totals. Each component reads only input or its immediate artifact; no synthetic final join.

Execution contract: generate executable local Dagster code without network access, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology; alternative node decomposition is allowed only when logical operations, checkpoints, and dependency semantics remain equivalent. Write under the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers/bounds, or non-finite required values fail clearly except for explicitly recoverable fields.

Mandatory output files:
- `prediction_data.csv`
- `all_star_model.pkl`
- `all_star_predictions.csv`
- `all_star_report.json`
- `position_statistics.csv`
- `position_report.json`
- `team_chart_data.csv`
- `team_chart_report.json`
