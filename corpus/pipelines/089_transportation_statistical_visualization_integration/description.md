# Independent service summaries converging into a portfolio report

Build a four-task pure fan-in graph. Three independent roots read the input and compute route, vehicle, and weather summaries of trip count, delay, on-time percentage, and satisfaction. A final task consumes all three artifacts, reconciles their trip totals, reports group counts, and identifies the best route by on-time descending, satisfaction descending, then route. The roots must not depend on one another.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `route_service.csv`
- `vehicle_service.csv`
- `weather_service.csv`
- `service_report.json`
