# Trip geography fanning out to route ranking and two summaries

Build a six-task linear-to-fan-out graph. Validate trips and coordinate bounds; compute haversine distance using Earth radius 6371.0088 km, passenger-geodesic-km, and four departure periods. Fan this shared geographic artifact into route aggregation followed by deterministic route ranking, vehicle geographic summary, and departure-period geographic summary. Vehicle and period leaves consume the trip-level artifact directly; the three terminal views do not join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_clean.csv`
- `trip_geography.csv`
- `route_geography.csv`
- `route_geography_ranking.csv`
- `vehicle_geography.csv`
- `period_geography.csv`
