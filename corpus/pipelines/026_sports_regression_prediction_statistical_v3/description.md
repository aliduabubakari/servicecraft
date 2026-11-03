# Shared player features feeding two models and a joint evaluation

Build a nine-task fan-in/fan-out graph. Validate players; independently derive performance features (production and shooting indices) and availability/context features; join them one-to-one. Fan the joined table to market-value Ridge regression using an 80/20 seed-42 split, alpha=1 and train-only scaling, and All-Star logistic classification using a stratified 75/25 seed-42 split, C=1, liblinear, threshold 0.5 and train-only scaling. Evaluate with MAE/RMSE/R2 and accuracy/precision/recall/F1/ROC AUC, then reconverge both metric artifacts into one report.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `performance_features.csv`
- `availability_features.csv`
- `model_data.csv`
- `market_model.pkl`
- `market_predictions.csv`
- `market_metrics.json`
- `allstar_model.pkl`
- `allstar_predictions.csv`
- `allstar_metrics.json`
- `dual_model_report.json`
