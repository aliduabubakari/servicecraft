# Route service metrics fanning out to three analyses

Build a linear-to-fan-out graph. Validate trips; derive service_score=(on_time_pct+passenger_satisfaction/5)/2 and passenger_km; aggregate route service metrics; then independently produce reliability ranking, satisfaction ranking, and a route-level association report. Each leaf consumes only route_service_metrics.csv, and the leaves do not join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Invalid identifiers, missing columns, or non-finite required values must fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `trip_service_features.csv`
- `route_service_metrics.csv`
- `reliability_ranking.csv`
- `satisfaction_ranking.csv`
- `service_associations.json`
