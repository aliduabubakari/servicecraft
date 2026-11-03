# Convergent route reliability and satisfaction scoring

Build `linear_to_fan_in`: independent route reliability and satisfaction roots read/validate trips. Reliability outputs counts, mean delay/on-time, sample delay SD. Satisfaction outputs counts, mean satisfaction/passengers/distance. Join one-to-one on route and equal trip_count; reliability_score=on_time_pct, satisfaction_score=satisfaction/5, combined=(both)/2. Rank descending combined then route ascending; report routes, reconciled trips, top route/score. The join must be followed by ranking and report.

Execution contract: generate executable local Dagster code without network access, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology; alternative node decomposition is allowed only when logical operations, checkpoints, and dependency semantics remain equivalent. Write under the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers/bounds, or non-finite required values fail clearly except for explicitly recoverable fields.

Mandatory output files:
- `route_reliability.csv`
- `route_satisfaction.csv`
- `route_scores.csv`
- `ranked_routes.csv`
- `route_report.json`
