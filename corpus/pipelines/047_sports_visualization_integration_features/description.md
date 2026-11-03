# Linear player features to position ranking

Build the sole five-task linear case. Validate players; derive production, safe production-per-minute, and value=production/(salary+1); summarize counts and mean features by position; rank by production descending, value descending, then position; report reconciled totals and the top position. Each task consumes only its immediate predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `player_features.csv`
- `position_summary.csv`
- `position_ranking.csv`
- `position_report.json`
