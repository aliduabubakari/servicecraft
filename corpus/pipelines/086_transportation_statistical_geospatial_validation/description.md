# Geographic and service route summaries converging for ranking

Build a six-task linear-to-fan-in graph. Two independent roots summarize each route: a geographic branch validates coordinate bounds and computes haversine/passenger-geodesic distance, while a service branch computes reported distance, delay, on-time and satisfaction means. Join one-to-one by route and require equal trip counts. Compute distance alignment and a route score weighted 0.40 on-time, 0.30 satisfaction/5, 0.20 inverse min-max delay, and 0.10 distance alignment; rank by score descending, on-time descending, then route; publish a final report. The scoring chain must consume the joined artifact.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `route_geography.csv`
- `route_service.csv`
- `route_context.csv`
- `route_scores.csv`
- `route_ranking.csv`
- `route_report.json`
