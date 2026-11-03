# All-Star modeling with convergent feature and diagnostic branches

Build 8-task fan-in/fan-out. Validate players; derive performance/production and injury/availability features independently; join one-to-one; fit a fixed 75/25 stratified seed-42 StandardScaler+LogisticRegression model; fan predictions to overall metrics and team diagnostics; reconverge into a report. Threshold is 0.5 and metrics are accuracy, precision, recall, F1, ROC AUC.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, or non-finite required values fail clearly.

Mandatory output files:
- `players_clean.csv`
- `performance_features.csv`
- `availability_features.csv`
- `model_data.csv`
- `model.pkl`
- `predictions.csv`
- `metrics.json`
- `team_diagnostics.csv`
- `model_report.json`
