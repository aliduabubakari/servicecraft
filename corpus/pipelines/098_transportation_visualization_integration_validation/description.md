# Independent operational summaries converging into a report

Build a four-task pure fan-in graph. Three independent roots compute route, vehicle, and weather summaries. Route and weather include passenger-km and on-time=(delay<=5); vehicle includes passenger, fare, and delay measures. A final task consumes all three artifacts and reconciles trip totals and group counts.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for explicitly documented recovery fixtures, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `route_operations.csv`
- `vehicle_operations.csv`
- `weather_operations.csv`
- `operations_report.json`
