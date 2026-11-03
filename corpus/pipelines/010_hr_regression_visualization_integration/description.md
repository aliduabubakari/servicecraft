# Integrated workforce features with three analytical outputs

Build a `linear_to_fan_out` workforce pipeline. Validate and integrate employee/department data, derive common features, then fan out to three independent leaves: salary regression, department summary, and gender pay summary. Do not add an artificial synthesis node.

Require unique nonblank emp_id and department keys, valid employee department membership, and finite numeric fields. Join employees many-to-one with departments and write workforce.csv sorted by emp_id. Derive salary_per_experience_year = salary/(experience_years+1) and budget_per_head_millions = budget_millions/headcount in workforce_features.csv.

Salary branch: predictors in order are experience_years, performance_score, age, headcount, budget_millions. Use an 80/20 random split with seed 42 and LinearRegression. Emit salary_model.pkl, sorted salary_predictions.csv, and salary_metrics.json with train/test rows, features, MAE, RMSE, and R2.

Department branch emits employee_rows, declared_headcount, budget_millions, mean_salary, and mean_performance_score by department. Gender branch emits employee_count, mean/median salary, and mean experience_years by gender. Both are sorted by group. These descriptive branches must consume workforce_features.csv directly and must not depend on the model branch.

Execution contract: generate executable local Dagster code. Do not use networks, external services, prior-run outputs, fixed analytical answers, or human intervention. The required topology is semantically necessary: independent branches must not consume one another's outputs, while every declared join must consume the listed branch artifacts. A different Dagster asset/op decomposition is allowed only if it preserves the logical tasks, data dependencies, topology class, and observable checkpoints. Write outputs beneath the run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid primary/foreign keys, invalid dates, or non-finite required values must fail clearly.

Mandatory output files:
- `workforce.csv`
- `workforce_features.csv`
- `salary_model.pkl`
- `salary_predictions.csv`
- `salary_metrics.json`
- `department_summary.csv`
- `gender_pay_summary.csv`
