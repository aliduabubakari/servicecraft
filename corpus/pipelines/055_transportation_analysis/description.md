# Linear transportation delay regression

Build the sole `linear` batch-04 pipeline: validate trips, engineer features, split, fit/predict, evaluate, and report. Require unique nonblank trip_id, departure_hour in [0,23], nonnegative finite distance/passengers/fare/delay, and binary is_holiday. Emit trips_clean.csv sorted by trip_id.

Derive fare_per_passenger (zero when passengers=0) and distance_holiday_interaction. Predict delay_minutes using ordered predictors departure_hour, distance_km, passengers, fare_amount, is_holiday, fare_per_passenger, distance_holiday_interaction. Use an 80/20 random split with seed 42, emitted partitions sorted by trip_id, train-only StandardScaler, and Ridge(alpha=1, solver=svd). Emit model and predictions for every test row. metrics.json and delay_report.json contain train/test rows, ordered features, MAE minutes, and RMSE minutes. Each task must consume the preceding task's artifact.

Execution contract: generate executable local Dagster code without network services, prior-run outputs, fixed analytical answers, or human intervention. The declared topology is a scored semantic property: preserve independent branches and every artifact-backed join. Alternative Dagster decomposition is allowed only when logical requirements, dependencies, topology, and observable checkpoints remain equivalent. Write outputs beneath the run output directory. Preserve numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid identifiers/dates, broken relationships, and non-finite required values must fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `trip_features.csv`
- `train.csv`
- `test.csv`
- `model.pkl`
- `predictions.csv`
- `metrics.json`
- `delay_report.json`
