# Linear position performance analysis

Build the sole linear case. Validate players; derive production_index, mean shooting_index and value_index=production/(salary+1); aggregate player counts and mean feature values by position; rank positions by mean production descending, mean shooting descending, then position; report the top position and reconciled totals. Each of five tasks consumes only its immediate predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `player_features.csv`
- `position_summary.csv`
- `position_ranking.csv`
- `position_report.json`
