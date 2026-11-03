# Valuation modeling with three feature branches and multiview diagnostics

Build a ten-task fan-in/fan-out graph. Validate players; independently derive production features, shooting features, and context/salary features; join all three one-to-one. From the integrated table, fit market-value Ridge regression using an 80/20 seed-42 split, alpha=1 and train-only scaling, while independently computing team and position diagnostics. Evaluate predictions with MAE, RMSE and R2, then reconverge metrics and both diagnostics into a report that reconciles player totals. Every branch must exchange the declared artifact.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `production_features.csv`
- `shooting_features.csv`
- `context_features.csv`
- `model_data.csv`
- `valuation_model.pkl`
- `valuation_predictions.csv`
- `valuation_metrics.json`
- `team_diagnostics.csv`
- `position_diagnostics.csv`
- `valuation_report.json`
