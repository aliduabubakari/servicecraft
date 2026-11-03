# Independent workforce, engagement, and performance analytics

Build three independent two-task analytics branches. The required `parallel` topology has no artifact dependency between branches: workforce attrition uses employees.csv, engagement trends use engagement_surveys.csv, and performance summaries use performance_reviews.csv. Employee IDs in the latter sources must be members of employees.csv, but that source is a validation lookup rather than an output dependency. Do not merge the three analytical tables.

Workforce branch: validate unique nonblank employee_id and binary is_attrited, retain the six named columns in workforce.csv sorted by employee_id, then group by department into employee_count, attrition_count, attrition_rate, mean_salary, and mean_job_satisfaction. attrition_report.json gives total employees, attrited employees, overall rate, and department count.

Engagement branch: parse dates and validate the five finite score fields. Compute engagement_composite as their row mean. Aggregate by employee into survey_count, mean_engagement_composite, latest_survey_date; separately group by YYYY-MM into survey_count and mean composite. engagement_report.json gives survey rows, surveyed employees, months, and overall mean composite.

Performance branch: validate finite review measures. Aggregate by employee into review_count, mean performance, mean goal achievement, and count/sum of promotion recommendations. Use employees.csv only to attach department, then summarize reviewed employees, performance, goal achievement, and recommendations by department. performance_report.json gives review rows, reviewed employees, department count, and overall mean performance.

All branch outputs are mandatory. Parallelism is part of RQ1: connecting one branch after another, or combining them through a synthetic final report, is dependency-incorrect.

Execution contract: generate executable local Dagster code. Do not use networks, external services, prior-run outputs, fixed analytical answers, or human intervention. The required topology is semantically necessary: independent branches must not consume one another's outputs, while every declared join must consume the listed branch artifacts. A different Dagster asset/op decomposition is allowed only if it preserves the logical tasks, data dependencies, topology class, and observable checkpoints. Write outputs beneath the run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid primary/foreign keys, invalid dates, or non-finite required values must fail clearly.

Mandatory output files:
- `workforce.csv`
- `attrition_by_department.csv`
- `attrition_report.json`
- `engagement_by_employee.csv`
- `engagement_by_month.csv`
- `engagement_report.json`
- `performance_by_employee.csv`
- `performance_by_department.csv`
- `performance_report.json`
