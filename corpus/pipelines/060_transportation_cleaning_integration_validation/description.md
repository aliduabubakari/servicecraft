# Validated trips fanning out to operational summaries

Build a four-task pure fan-out graph. Validate trips and derive passenger_km=distance*passengers and on_time=(delay<=5) in one shared artifact. Three independent leaves consume only that artifact: route passenger-km/delay/on-time metrics, vehicle passenger/fare/delay metrics, and weather delay/on-time metrics. Do not add a final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_clean.csv`
- `route_operations.csv`
- `vehicle_operations.csv`
- `weather_operations.csv`
