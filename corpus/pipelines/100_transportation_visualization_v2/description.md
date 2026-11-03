# Linear route performance ranking and chart preparation

Build the sole five-task linear case. Validate trips and derive passenger-km plus on_time=(delay<=5); aggregate route trip count, passenger-km, passengers, fare, delay, and on-time rate; rank by total passenger-km descending, on-time descending, then route; prepare ordered chart data and passenger-km labels; report reconciled totals and the leading route. Every task consumes only its immediate predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for the explicitly documented recovery fixture, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `trips_prepared.csv`
- `route_summary.csv`
- `route_ranking.csv`
- `route_chart_data.csv`
- `route_report.json`
