# Convergent All-Star feature branches with diagnostic fan-out

Build 9-task `fan_in_fan_out`. Validate players, then independently derive performance features (ten source measures plus production_index) and shooting features (three percentages plus shooting_index). Join branches one-to-one with player/team/position/target. Fit 75/25 stratified seed-42 train-only StandardScaler+LogisticRegression(C=1, liblinear, max_iter=1000), threshold 0.5, emitting predictions/model. Fan predictions to overall metrics, position diagnostic rates, and five equal-width probability calibration bins. Final report consumes all three diagnostics.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies. Alternative decomposition is acceptable only when logical tasks, checkpoints, and dependency semantics remain equivalent. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, and non-finite required values fail clearly.

Mandatory output files:
- `players_clean.csv`
- `performance_features.csv`
- `shooting_features.csv`
- `model_data.csv`
- `model.pkl`
- `predictions.csv`
- `metrics.json`
- `position_model_summary.csv`
- `calibration_bins.csv`
- `allstar_report.json`
