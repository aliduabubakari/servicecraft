# Student GPA regression with explicit feature and evaluation stages

Build the batch's sole `linear` pipeline: validate student records, derive features, split, fit/predict, evaluate, and report. Require unique nonblank student_id, finite numeric fields, attendance in [0,100], and previous/current GPA in [0,4]. Sort students_clean.csv by student_id.

Derive study_attendance_interaction = study_hours_per_week*attendance_pct/100 and gpa_change = current_gpa-previous_gpa. The target is current_gpa; gpa_change is retained for audit but must not be a predictor. Use predictors in this order: year, age, study_hours_per_week, attendance_pct, previous_gpa, assignments_completed, extracurricular_hours, study_attendance_interaction.

Create an 80/20 random split with seed 42 and sort the emitted train.csv/test.csv by student_id. Fit StandardScaler on training predictors only, then Ridge(alpha=1, solver=svd). Emit model.pkl and predictions.csv for every test student. metrics.json contains train/test counts, ordered features, MAE, and RMSE; student_report.json publishes exactly those computed values. Every stage consumes the preceding stage's artifacts.

Execution contract: generate executable local Dagster code. Do not use networks, external services, prior-run outputs, fixed analytical answers, or human intervention. The required topology is semantically necessary: independent branches must not consume one another's outputs, while every declared join must consume the listed branch artifacts. A different Dagster asset/op decomposition is allowed only if it preserves the logical tasks, data dependencies, topology class, and observable checkpoints. Write outputs beneath the run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid primary/foreign keys, invalid dates, or non-finite required values must fail clearly.

Mandatory output files:
- `students_clean.csv`
- `student_features.csv`
- `train.csv`
- `test.csv`
- `model.pkl`
- `predictions.csv`
- `metrics.json`
- `student_report.json`
