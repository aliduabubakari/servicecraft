# Transportation spatial enrichment and route aggregation

Build a local Dagster pipeline for spatial enrichment of transportation trips and route-level analysis. It requires actual spherical distance computation and grouped summaries, with no machine learning or visualization.

Read `data.csv`. Use trip_id, route, origin_lat, origin_lon, dest_lat, dest_lon, distance_km, passengers, and delay_minutes; ignore other columns. Strip whitespace from trip_id/route and treat blanks as missing. Coerce numeric text to numbers. Reject a row if either string is missing, its normalized trip_id repeats after the first input occurrence, any required numeric value is missing/non-finite, latitude is outside [-90,90], longitude outside [-180,180], distance_km/passengers/delay_minutes is negative, or passengers is not an integer. A duplicate's first occurrence is defined before validity filtering. Do not impute invalid coordinates or clip them. Keep rejected rows in rejected_trips.csv and record input_rows, valid_rows, and rejected_rows in validation.json.

For valid trips compute great_circle_km using the haversine formula on origin/destination coordinates in degrees with spherical Earth radius 6371.0088 km. Clip the formula's intermediate a to [0,1] before computing 2R*asin(sqrt(a)). Compute passenger_km = distance_km * passengers and detour_ratio = distance_km / great_circle_km. If great_circle_km is exactly zero, write a missing detour_ratio rather than infinity. distance_km is a supplied traveled distance; do not replace it with spherical distance. Synthetic trips may have detour_ratio below one, which must not be clipped or rejected. Sort trip_metrics.csv by trip_id.

Group valid enriched trips by normalized route. For each route output trip_count, mean_great_circle_km, total_passenger_km, and mean_delay_minutes. Sort route_summary.csv by route. Produce spatial_report.json with quality (the input/valid/rejected counts), earth_radius_km, route_count, total_passenger_km over all valid trips, mean_great_circle_km over all valid trips (null for an empty set), and top_routes containing up to five route names ranked by descending trip_count with lexicographically ascending route as the tie-breaker. Empty valid data must yield an empty route table, zero total passenger-km, null mean distance, and an empty top_routes array.

Validation precedes spatial enrichment, route aggregation consumes enriched trips, and reporting consumes the computed aggregation. Preserve validation and spatial metadata through the intermediate JSON artifacts listed below. Every required result must come from the current run.

Execution and output contract: generate executable Dagster code using local files, without network access or external services. Each mandatory logical operation must be inspectable in the pipeline design/code. A different task decomposition is allowed if it preserves the stated behavior, dependencies, and observable intermediate outputs. Write outputs beneath the designated run output directory. Do not read outputs from previous runs. Preserve full numeric precision in CSV/JSON; numeric comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity; missing CSV values may use empty cells. Required JSON counts are integers. Files listed below are mandatory checkpoints and results, not prescriptions for the number of Dagster assets. Missing input columns fail clearly.

Mandatory output files:
- `valid_trips.csv` (required columns: trip_id, route, origin_lat, origin_lon, dest_lat, dest_lon, distance_km, passengers, delay_minutes)
- `rejected_trips.csv` (required columns: trip_id)
- `validation.json`
- `trip_metrics.csv` (required columns: trip_id, great_circle_km, passenger_km, detour_ratio)
- `spatial_metadata.json`
- `route_summary.csv` (required columns: route, trip_count, mean_great_circle_km, total_passenger_km, mean_delay_minutes)
- `aggregate.json`
- `spatial_report.json`
