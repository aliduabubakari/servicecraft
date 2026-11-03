# Validated workforce data with independent analytical leaves

Build a pure `fan_out` workforce DAG. One root task validates unique nonblank employee IDs, finite measures, nonnegative tenure/salary/bonus/age, and performance_score in [1,5]. It derives total_compensation=salary+bonus and emits workforce_clean.csv sorted by emp_id. That root artifact must fan directly into three independent leaf tasks; do not add a synthetic final join.

The compensation leaf groups by department and emits employee_count, mean_salary, median_salary, total_bonus, and mean_total_compensation. The performance leaf groups by department and emits employee_count, mean_performance_score, high_performer_count (score >=4), and mean_tenure_years. The composition leaf groups by status and gender and emits employee_count, mean_age, and mean_tenure_years. Sort grouped outputs lexicographically by their keys. All three leaves are mandatory and must depend only on workforce_clean.csv.

Execution contract: generate executable local Dagster code without network services, prior-run outputs, fixed analytical answers, or human intervention. The declared topology is a scored semantic property: preserve independent branches and every artifact-backed join. Alternative Dagster decomposition is allowed only when logical requirements, dependencies, topology, and observable checkpoints remain equivalent. Write outputs beneath the run output directory. Preserve numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid identifiers/dates, broken relationships, and non-finite required values must fail clearly.

Mandatory output files:
- `workforce_clean.csv`
- `compensation_by_department.csv`
- `performance_by_department.csv`
- `workforce_composition.csv`
