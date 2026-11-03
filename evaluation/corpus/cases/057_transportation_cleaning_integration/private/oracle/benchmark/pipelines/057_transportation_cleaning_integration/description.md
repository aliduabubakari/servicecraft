# Linear route performance ranking

Build the sole linear pipeline: validate trips; derive passenger_km, fare_per_passenger, on_time=(delay<=5); aggregate routes into trip count, total passenger-km, mean fare/passenger, on-time rate, mean delay; rank by on-time descending, passenger-km descending, route ascending; publish trips/routes/top route/top rate. Five tasks, each consuming only its predecessor artifact.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies. Alternative decomposition is acceptable only when logical tasks, checkpoints, and dependency semantics remain equivalent. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, and non-finite required values fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `trip_features.csv`
- `route_metrics.csv`
- `ranked_routes.csv`
- `route_performance_report.json`
