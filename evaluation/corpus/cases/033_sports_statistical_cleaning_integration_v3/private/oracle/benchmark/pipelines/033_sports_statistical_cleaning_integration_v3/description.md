# Linear player shooting and value ranking

Build the sole linear pipeline. Validate players; derive shooting_index, production_index, and value_index; rank by shooting descending, production descending, then player ID; select the top three players per position; and publish counts plus the overall leader. Each of five tasks consumes only its immediate predecessor.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Invalid identifiers, missing columns, or non-finite required values must fail clearly.

Mandatory output files:
- `players_clean.csv`
- `player_scores.csv`
- `ranked_players.csv`
- `position_leaders.csv`
- `ranking_report.json`
