# Route economics and service metrics fanning out to three analyses

Build a six-task linear-to-fan-out graph. Validate trips; derive profit=revenue-cost, safe profit margin, service_score=(on_time+satisfaction/5)/2, and passenger-km; aggregate route revenue, cost, profit, margin, service, delay and passenger-km. Fan that shared route table into deterministic profitability ranking, deterministic service ranking, and a trade-off report containing route/trip totals plus profit-service and margin-delay correlations. Leaves consume only route_metrics.csv and do not join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_clean.csv`
- `trip_economics.csv`
- `route_metrics.csv`
- `profitability_ranking.csv`
- `service_ranking.csv`
- `route_tradeoffs.json`
