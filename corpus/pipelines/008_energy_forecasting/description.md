# Energy demand regression with lagged weather and chronological evaluation

Build a local Dagster pipeline to evaluate historical hourly energy demand regression with lagged information. The target is exactly consumption_kwh. This evaluates fixed-model rolling prediction with observed lagged consumption, not recursive multi-hour forecasting or a production forecast service.

Read energy_consumption.csv (timestamp, consumption_kwh, is_holiday) and weather.csv (date, temp_avg, humidity_avg, cloud_cover_avg, wind_avg); ignore all other fields. Parse timestamps/dates, sort energy by timestamp and weather by date, and fail on duplicate timestamps/dates, missing or non-finite required numeric values, negative consumption, or holiday flags outside {0,1}. Energy observations must be continuous at one-hour intervals. Dates are timezone-naive and weather.date is a calendar-day key. Inputs that violate these preconditions fail clearly; do not silently fill or drop malformed source observations.

For each energy observation on date D, left-join weather from D-1 using one daily weather row per key. Name the joined fields previous_temp_avg, previous_humidity_avg, previous_cloud_cover_avg, previous_wind_avg. Do not use same-day or future weather, the hourly weather fields embedded in energy_consumption.csv, or weather.is_holiday. Derive lag_24h_kwh from consumption exactly 24 preceding hourly rows, hour (0-23), day_of_week (Monday=0), and month (1-12). Use the energy input's is_holiday unchanged. After deriving lag/joins, omit feature rows missing any required predictor. Require at least 10 eligible observations.

Use exactly these predictors in this order: lag_24h_kwh, hour, day_of_week, month, is_holiday, previous_temp_avg, previous_humidity_avg, previous_cloud_cover_avg, previous_wind_avg. Retain timestamp and consumption_kwh for audit but exclude them from predictors. Sort chronologically and split the eligible rows at floor(0.8*N): earliest rows train, remaining rows test. Do not shuffle. Lagged consumption in later test observations may use earlier observed consumption from the test period, because this is rolling prediction, not a recursive forecast.

Fit StandardScaler (population variance, ddof=0) on training predictors only, then Ridge regression with alpha=1, fit_intercept=True, and solver=svd on the scaled training predictors and training target. Reuse the fitted scaler on test data. Save a pickle of the fitted pipeline and fit_metadata.json with train_rows, test_rows, the ordered feature list, alpha, scaler_mean, and scaler_scale. Do not fit preprocessing on all data or include the target as a predictor.

Write predictions.csv containing timestamp, actual_kwh, predicted_kwh for every test row in chronological order. Compute MAE and RMSE in kWh directly from these held-out predictions. metrics.json must include the fit metadata plus mae_kwh and rmse_kwh. energy_report.json must publish those computed values. Preserve the intermediate aligned/feature/train/test tables so lag choice, split boundary, and leakage can be independently checked. This task specifies an estimator and procedure, rather than a loose model-quality threshold.

Execution and output contract: generate executable Dagster code using local files, without network access or external services. Each mandatory logical operation must be inspectable in the pipeline design/code. A different task decomposition is allowed if it preserves the stated behavior, dependencies, and observable intermediate outputs. Write outputs beneath the designated run output directory. Do not read outputs from previous runs. Preserve full numeric precision in CSV/JSON; numeric comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity; missing CSV values may use empty cells. Required JSON counts are integers. Files listed below are mandatory checkpoints and results, not prescriptions for the number of Dagster assets. Missing input columns fail clearly.

Mandatory output files:
- `hourly.csv` (required columns: timestamp, consumption_kwh, is_holiday)
- `daily_weather.csv` (required columns: date, temp_avg, humidity_avg, cloud_cover_avg, wind_avg)
- `aligned.csv` (required columns: timestamp, previous_temp_avg)
- `features.csv` (required columns: timestamp, consumption_kwh, lag_24h_kwh, hour, day_of_week, month, is_holiday, previous_temp_avg, previous_humidity_avg, previous_cloud_cover_avg, previous_wind_avg)
- `train.csv` (required columns: timestamp, consumption_kwh)
- `test.csv` (required columns: timestamp, consumption_kwh)
- `model.pkl`
- `predictions.csv` (required columns: timestamp, actual_kwh, predicted_kwh)
- `fit_metadata.json`
- `metrics.json`
- `energy_report.json`
