# Linear team performance ranking and chart preparation

Build the sole five-task linear case. Validate players and derive production plus safe production-per-minute; aggregate team counts and mean performance, salary and experience; rank by production descending, per-minute production descending, then team; prepare ordered chart data and labels; report reconciled totals and the top team. Every task consumes only its immediate predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_prepared.csv`
- `team_summary.csv`
- `team_ranking.csv`
- `team_chart_data.csv`
- `team_report.json`
