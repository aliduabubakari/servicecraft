# Parallel delay classification and cancellation-risk regression

Build two disconnected three-task components over independently prepared artifacts. Both use departure hour, distance, passengers, fare and holiday as numeric predictors and route, vehicle, weekday and weather as categorical predictors. Delay classification uses a fixed stratified 75/25 seed-42 split, train-only preprocessing, LogisticRegression (C=1, liblinear), threshold 0.5, and five metrics. Cancellation-risk regression separately uses a fixed 75/25 seed-42 split, the same train-only preprocessing, Ridge(alpha=1), and MAE/RMSE/R2. Neither component consumes the other's artifacts.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `delay_model_data.csv`
- `delay_model.pkl`
- `delay_predictions.csv`
- `delay_metrics.json`
- `risk_model_data.csv`
- `risk_model.pkl`
- `risk_predictions.csv`
- `risk_metrics.json`
