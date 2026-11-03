# Prepared trips fanning out to three operational views

Build a pure fan-out graph. One root validates trips and derives passenger_km and on_time=(delay_minutes<=5). Three independent leaves consume only that prepared artifact and summarize route passenger-km/delay/on-time performance, vehicle passenger/fare/delay behavior, and weather delay/on-time behavior. There is no final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Invalid identifiers, missing columns, or non-finite required values must fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `route_operations.csv`
- `vehicle_operations.csv`
- `weather_operations.csv`
