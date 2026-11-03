# Parallel spatial and service-quality transportation analyses

Build two disconnected three-task components. Spatial component validates coordinates, computes haversine great_circle_km with radius 6371.0088 and traveled/great-circle ratio, summarizes by route, then reports trip/route counts and mean distance. Service component independently computes service_score=(on_time_pct+satisfaction/5)/2, groups by vehicle/weather into count and mean score/delay/passengers, then reports trip/group counts and overall mean. No artifact crosses components.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies. Alternative decomposition is acceptable only when logical tasks, checkpoints, and dependency semantics remain equivalent. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, and non-finite required values fail clearly.

Mandatory output files:
- `trip_spatial_metrics.csv`
- `route_spatial_summary.csv`
- `spatial_report.json`
- `trip_service_metrics.csv`
- `service_group_summary.csv`
- `service_report.json`
