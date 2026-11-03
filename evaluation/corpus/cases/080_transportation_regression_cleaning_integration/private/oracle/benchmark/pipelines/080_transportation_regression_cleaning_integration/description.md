# Revenue and cost feature branches converging into route economics

Build a six-task linear-to-fan-in graph. Independent roots derive revenue features (fare-revenue proxy and revenue per passenger) and cost features (cost per kilometre and cost per passenger). Join one-to-one by trip and compute profit and safe margin; aggregate route revenue, cost, profit, margin and unit measures; rank by profit descending, margin descending, then route; report portfolio totals and the leader. All downstream work consumes the joined artifact.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `revenue_features.csv`
- `cost_features.csv`
- `trip_economics.csv`
- `route_economics.csv`
- `route_ranking.csv`
- `economics_report.json`
