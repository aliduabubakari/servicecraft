# Route economics and service summaries converging for composite ranking

Build a six-task linear-to-fan-in graph. Independent roots aggregate route economics (revenue, cost, profit, margin, passenger-km) and route service (delay, on-time, satisfaction). Join one-to-one by route and require equal trip counts. Compute a composite score weighted 0.35 min-max profit, 0.30 on-time, 0.20 satisfaction/5, and 0.15 inverse min-max delay; rank by score descending, profit descending, then route; publish the leader and totals. The scoring chain consumes the joined artifact.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `route_economics.csv`
- `route_service.csv`
- `route_context.csv`
- `route_scores.csv`
- `route_ranking.csv`
- `route_report.json`
