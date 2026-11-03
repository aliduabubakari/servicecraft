# Prepared trips with three operational views

Build pure fan-out. Root validates trips and derives passenger_km and on_time=(delay<=5). Three leaves independently summarize route passenger-km/delay/on-time, vehicle passenger/fare/delay, and weather delay/on-time. No final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, or non-finite required values fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `route_operations.csv`
- `vehicle_operations.csv`
- `weather_operations.csv`
