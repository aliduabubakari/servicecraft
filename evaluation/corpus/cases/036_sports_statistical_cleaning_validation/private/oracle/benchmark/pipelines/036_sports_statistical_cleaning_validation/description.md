# Linear shooting-efficiency and value ranking

Build the sole linear case. Validate players; compute shooting_index as the mean of three shooting percentages, production_index as points+assists+rebounds, and value_index as production/(salary+1); rank by shooting descending, production descending, then player ID; select the top three per position; and report counts plus the overall leader. Each task consumes only its immediate predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `player_scores.csv`
- `ranked_players.csv`
- `position_leaders.csv`
- `ranking_report.json`
