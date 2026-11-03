# Trip economics fanning out to three operational views

Build a six-task linear-to-fan-out graph. Validate trips; derive profit=revenue-cost, safe profit margin and passenger-km. Fan that shared trip-level artifact into route aggregation followed by deterministic profitability ranking, an independent vehicle economics summary, and an independent weather economics summary. The three terminal views do not join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_clean.csv`
- `trip_economics.csv`
- `route_economics.csv`
- `route_profitability.csv`
- `vehicle_economics.csv`
- `weather_economics.csv`
