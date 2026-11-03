# Recovered trip data with independent route, vehicle, and weather views

Build pure fan-out. Validate unique trip_id. Normalize strings, replacing missing vehicle/weather with `Unknown`. For passengers, fare_amount, delay_minutes, coerce invalid to missing and recover from route median computed from valid values, then global median, then zero. Preserve all rows, sort by trip_id, and emit audit counts. The benchmark fixture contains exactly one missing value in each numeric recovery field and one missing value in each categorical recovery field.

Three independent leaves consume recovered trips: route summary (count, mean passengers/fare/delay), vehicle summary (count, mean distance/passengers/delay), and weather summary (count, mean delay/fare). Sort keys and do not add a final join.

Execution contract: generate executable local Dagster code without network access, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology; alternative node decomposition is allowed only when logical operations, checkpoints, and dependency semantics remain equivalent. Write under the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers/bounds, or non-finite required values fail clearly except for explicitly recoverable fields.

Mandatory output files:
- `trips_recovered.csv`
- `recovery_audit.json`
- `route_summary.csv`
- `vehicle_summary.csv`
- `weather_summary.csv`
