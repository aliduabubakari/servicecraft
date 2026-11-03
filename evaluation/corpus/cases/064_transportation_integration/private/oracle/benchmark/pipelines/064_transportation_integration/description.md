# Prepared trips fanning out to route, weekday, and weather summaries

Build a four-task pure fan-out graph. One root validates trips and derives passenger-km and on_time=(delay<=5). Three independent leaves consume only that artifact and summarize route passenger-km/delay/on-time, weekday passengers/delay/on-time, and weather passenger-km/delay/on-time. There is no final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_clean.csv`
- `route_operations.csv`
- `weekday_operations.csv`
- `weather_operations.csv`
