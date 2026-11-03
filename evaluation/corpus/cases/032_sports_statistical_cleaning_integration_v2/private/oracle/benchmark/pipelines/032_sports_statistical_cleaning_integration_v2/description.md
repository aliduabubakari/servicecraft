# Linear shooting-efficiency ranking

Build the sole linear case: validate; derive shooting_index, production_index, value_index; rank by shooting descending, production descending, player ID; select top three per position; report counts and overall leader. Five tasks, each consuming only its predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, or non-finite required values fail clearly.

Mandatory output files:
- `players_clean.csv`
- `player_scores.csv`
- `ranked_players.csv`
- `position_leaders.csv`
- `ranking_report.json`
