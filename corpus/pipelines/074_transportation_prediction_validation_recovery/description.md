# Recovered delay modeling with multiview diagnostics

Build an eleven-task fan-in/fan-out graph over the supplied defect-bearing fixture. Audit four missing-input flags; recover distance and fare with route median then global median and recover vehicle/weather with deterministic global modes. Independently derive operational and context features, join one-to-one, and fit delay classification using a fixed stratified 75/25 seed-42 split, train-only preprocessing, LogisticRegression (C=1, liblinear), and threshold 0.5. Evaluate five metrics; compute route, weather, and vehicle diagnostics; reconverge recovery audit, metrics, and diagnostics into a report. The four defects are one distance, one fare, one vehicle, and one weather value.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for explicitly documented recovery fixtures, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `audited_trips.csv`
- `trips_recovered.csv`
- `recovery_audit.json`
- `operational_features.csv`
- `context_features.csv`
- `model_data.csv`
- `delay_model.pkl`
- `delay_predictions.csv`
- `delay_metrics.json`
- `route_diagnostics.csv`
- `weather_diagnostics.csv`
- `vehicle_diagnostics.csv`
- `delay_report.json`
