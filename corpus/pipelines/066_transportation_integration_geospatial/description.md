# Geographic trips fanning out to route, vehicle, and period views

Build a four-task pure fan-out graph. The root validates identifiers, categories and coordinate bounds; computes haversine distance with Earth radius 6371.0088 km, passenger-geodesic-km, and one of four departure periods (night, morning, afternoon, evening). Three independent leaves consume only that artifact and summarize route distance/delay, vehicle distance/passengers/fare, and period distance/delay/passengers. Do not add a final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_geographic.csv`
- `route_geography.csv`
- `vehicle_geography.csv`
- `period_geography.csv`
