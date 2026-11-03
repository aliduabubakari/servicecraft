# Route service metrics with three independent outputs

Build linear-to-fan-out. Validate trips; derive service_score=(on_time+satisfaction/5)/2 and passenger_km; aggregate route metrics; fan out to reliability ranking, satisfaction ranking, and route-level association report. Leaves consume only route_service_metrics.csv and do not join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, or non-finite required values fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `trip_service_features.csv`
- `route_service_metrics.csv`
- `reliability_ranking.csv`
- `satisfaction_ranking.csv`
- `service_associations.json`
