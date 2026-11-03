# Prepared trips fanning out to route, period, and weather views

Build a four-task pure fan-out graph. One root validates trips and derives passenger-km, on_time=(delay<=5), and four departure periods: night 0-5, morning 6-11, afternoon 12-17, evening 18-23. Three independent leaves consume only that artifact and summarize route, departure-period, and weather operations. There is no final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_prepared.csv`
- `route_operations.csv`
- `period_operations.csv`
- `weather_operations.csv`
