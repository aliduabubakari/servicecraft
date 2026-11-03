# Patient readmission integration with model and descriptive branches

Build a `fan_in_fan_out` patient-analysis DAG. Four independently prepared sources converge into patient_features.csv. That table fans out to a fixed readmission model, a utilization comparison, and an insurance-group clinical summary. The three results reconverge into readmission_report.json. This is an experimental benchmark, not clinical guidance.

Require unique nonblank patient_id and admission_id keys, valid foreign keys from all events to patients and from labs/medications to admissions, finite required measures, and binary readmitted_30d. Emit patients_clean.csv. Aggregate admissions per patient into count, total/mean length of stay, ICU count, procedures, and ER count; labs into count, abnormal count, and mean test value; medications into record count and unique medication count.

Left-join all three summaries one-to-one to patients and fill absent aggregate measures with zero. Retain patient demographics, insurance_type, target, and all aggregate features in patient_features.csv sorted by patient_id.

Model branch: use the specified numeric patient and aggregate features, a 75/25 stratified split with seed 42, train-only StandardScaler, and LogisticRegression(C=1, liblinear, max_iter=1000, seed 42). Threshold at 0.5 and emit model.pkl, predictions.csv, and accuracy/precision/recall/F1/ROC-AUC in readmission_metrics.json.

Utilization branch groups by readmitted_30d into patient count and means for admission count, total stay, and ER count. Clinical branch groups by insurance_type into patient count, readmission rate, mean abnormal-lab count, and mean unique medications. The final report publishes source counts, nested model metrics, and group counts; it must consume all three branch results.

Execution contract: generate executable local Dagster code. Do not use networks, external services, prior-run outputs, fixed analytical answers, or human intervention. The required topology is semantically necessary: independent branches must not consume one another's outputs, while every declared join must consume the listed branch artifacts. A different Dagster asset/op decomposition is allowed only if it preserves the logical tasks, data dependencies, topology class, and observable checkpoints. Write outputs beneath the run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid primary/foreign keys, invalid dates, or non-finite required values must fail clearly.

Mandatory output files:
- `patients_clean.csv`
- `admissions_by_patient.csv`
- `labs_by_patient.csv`
- `medications_by_patient.csv`
- `patient_features.csv`
- `model.pkl`
- `predictions.csv`
- `readmission_metrics.json`
- `utilization_by_readmission.csv`
- `clinical_summary.csv`
- `readmission_report.json`
