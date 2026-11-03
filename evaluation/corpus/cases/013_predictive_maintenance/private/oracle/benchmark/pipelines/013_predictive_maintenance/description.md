# Temporal maintenance features with dual-horizon failure models

Build a `fan_in_fan_out` predictive-maintenance DAG. Validate unique nonblank (machine_id,timestamp), hourly continuity within each machine, finite sensor fields, and binary targets; emit sensor_clean.csv sorted by machine/timestamp.

The clean table fans out into two past-only feature branches. Temporal branch computes lag-1 and prior-24-hour rolling means for temperature, vibration, and power. Baseline branch computes prior expanding mean and population standard deviation for temperature and vibration with minimum 24 observations. Both use shift(1), so the current/future row is excluded. Their outputs join one-to-one with clean sensors; drop rows missing any derived field and sort maintenance_features.csv by timestamp/machine.

The integrated table fans out to: (1) a 24-hour failure classifier, (2) a 7-day classifier, and (3) machine risk summary. Models share the ordered current/derived numeric predictors, earliest floor(0.8*N) rows for training, remaining rows for testing, train-only StandardScaler, LogisticRegression(C=1, liblinear, max_iter=1000, seed 42), and threshold 0.5. Each emits model, predictions, and accuracy/precision/recall/F1/ROC-AUC metrics. Risk summary reports observation/failure counts, target rates, and mean temperature/vibration by machine.

maintenance_report.json reconverges both metric artifacts and machine_risk_summary.csv, publishing integrated rows, machine count, nested metrics, and the highest seven-day-risk machine with machine_id ascending tie-breaker.

Execution contract: generate executable local Dagster code without network services, prior-run outputs, fixed analytical answers, or human intervention. The declared topology is a scored semantic property: preserve independent branches and every artifact-backed join. Alternative Dagster decomposition is allowed only when logical requirements, dependencies, topology, and observable checkpoints remain equivalent. Write outputs beneath the run output directory. Preserve numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid identifiers/dates, broken relationships, and non-finite required values must fail clearly.

Mandatory output files:
- `sensor_clean.csv`
- `temporal_features.csv`
- `expanding_baselines.csv`
- `maintenance_features.csv`
- `failure24h_model.pkl`
- `failure24h_predictions.csv`
- `failure24h_metrics.json`
- `failure7d_model.pkl`
- `failure7d_predictions.csv`
- `failure7d_metrics.json`
- `machine_risk_summary.csv`
- `maintenance_report.json`
