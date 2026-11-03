# Parallel market-value regression and All-Star classification

Build two disconnected three-task modeling components. The market-value component prepares declared predictors, uses a fixed 80/20 seed-42 split and train-only StandardScaler+LinearRegression, then reports MAE, RMSE, and R2. The All-Star component independently prepares its declared predictors, uses a fixed stratified 75/25 seed-42 split and train-only StandardScaler+LogisticRegression (C=1, liblinear), applies threshold 0.5, then reports accuracy, precision, recall, F1, and ROC AUC. Neither component consumes artifacts from the other.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Invalid identifiers, missing columns, or non-finite required values must fail clearly.

Mandatory output files:
- `regression_data.csv`
- `market_model.pkl`
- `market_predictions.csv`
- `market_metrics.json`
- `classification_data.csv`
- `allstar_model.pkl`
- `allstar_predictions.csv`
- `allstar_metrics.json`
