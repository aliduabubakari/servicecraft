# Credit-default classification with multi-source history aggregation

Build a local Dagster pipeline that estimates default risk from three related sources using one fixed, reproducible classifier. This is an experimental benchmark, not a lending decision system, fairness audit, or regulatory-compliance claim.

Validate that application_id is unique in applications.csv and bureau_data.csv, both contain the same identifier set, and every credit_history.csv identifier occurs in applications.csv. The target default_flag must be 0 or 1. Use exactly the named columns; required numeric fields must be finite.

Aggregate credit history by application_id into history_record_count, history_mean_utilization_pct, history_max_balance, and history_current_account_count, where current means account_status equals the case-sensitive literal Current. Inner-join the application and bureau tables one-to-one, then left-join the history summary one-to-one. Sort integrated.csv by application_id.

Use every numeric column in integrated.csv except application_id and default_flag as the ordered predictors. Create a 75/25 stratified random split with random_state=42. Sort each resulting partition by application_id for output. Fit StandardScaler on training predictors only and LogisticRegression with C=1.0, solver=liblinear, max_iter=1000, random_state=42. Predict test probabilities and classify with probability >= 0.5.

predictions.csv must contain application_id, actual_default, default_probability, and predicted_default. fit_metadata.json records train/test rows, ordered features, split fraction, seed, and threshold. Compute accuracy, precision, recall, F1, and ROC AUC from the held-out predictions, with zero_division=0 for precision/recall/F1. metrics.json and credit_report.json contain metadata plus those computed metrics.

Execution and output contract: generate executable Dagster code using only the supplied local files. Do not use network services, outputs from earlier runs, fixed analytical results, or human intervention. Each mandatory logical operation must be visible in the design/code. A different Dagster asset/op decomposition is allowed when it preserves the specified behavior, dependencies, and observable outputs. Write every output beneath the designated run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity. Missing required columns, broken identifier relationships, duplicate primary identifiers, invalid dates, and missing/non-finite required values must fail clearly.

Mandatory output files:
- `integrated.csv`
- `train.csv`
- `test.csv`
- `model.pkl`
- `predictions.csv`
- `fit_metadata.json`
- `metrics.json`
- `credit_report.json`
