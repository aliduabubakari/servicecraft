# Player valuation with convergent features and multiview diagnostics

Build a nine-task fan-in/fan-out graph. Validate players; independently derive production/per-minute performance and availability/context features; join one-to-one. From the joined artifact, fit market-value Ridge regression using an 80/20 seed-42 split, alpha=1 and train-only scaling; independently compute team diagnostics and position diagnostics. Evaluate held-out predictions with MAE, RMSE and R2, then reconverge metrics plus both diagnostic tables into a report that reconciles player counts.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `performance_features.csv`
- `context_features.csv`
- `model_data.csv`
- `market_model.pkl`
- `market_predictions.csv`
- `market_metrics.json`
- `team_diagnostics.csv`
- `position_diagnostics.csv`
- `valuation_report.json`
