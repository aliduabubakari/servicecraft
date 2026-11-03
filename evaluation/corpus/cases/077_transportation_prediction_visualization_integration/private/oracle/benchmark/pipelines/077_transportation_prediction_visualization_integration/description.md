# Delay modeling with convergent features and multiview diagnostics

Build a ten-task fan-in/fan-out graph. Validate trips; independently derive operational numeric features and categorical/target context; join one-to-one. Fit delay classification using a fixed stratified 75/25 seed-42 split, train-only scaling/one-hot encoding, LogisticRegression (C=1, liblinear), and threshold 0.5. From the integrated artifact, independently compute route, weather, and vehicle-risk diagnostics; evaluate predictions with accuracy, precision, recall, F1 and ROC AUC; reconverge metrics and all diagnostics into a report that reconciles trip totals.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for the explicitly documented recovery fixture, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_clean.csv`
- `operational_features.csv`
- `context_features.csv`
- `model_data.csv`
- `delay_model.pkl`
- `delay_predictions.csv`
- `delay_metrics.json`
- `route_diagnostics.csv`
- `weather_diagnostics.csv`
- `vehicle_risk_diagnostics.csv`
- `delay_report.json`
