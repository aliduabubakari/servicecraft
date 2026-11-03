# Prepared trips fanning out to route, vehicle, and period views

Build a four-task pure fan-out graph. One root validates trips and derives passenger-km, on_time=(delay<=5), and four departure periods. Three independent leaves consume only that artifact and summarize route passenger-km/delay/on-time, vehicle passengers/fare/delay, and departure-period passenger-km/delay/on-time. There is no final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for the explicitly documented recovery fixture, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_prepared.csv`
- `route_operations.csv`
- `vehicle_operations.csv`
- `period_operations.csv`
