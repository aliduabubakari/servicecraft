# Linear player production ranking

Build the sole linear pipeline: validate unique players and finite values; derive production_index=points+assists+rebounds, shooting_index=mean of three percentages, and per_minute_production=production/minutes; rank descending production, descending shooting, player_id ascending; select first five ranked players per position; publish player/position/top-row counts and overall leader. Each of five tasks consumes only its predecessor artifact.

Execution contract: generate executable local Dagster code without network access, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology; alternative node decomposition is allowed only when logical operations, checkpoints, and dependency semantics remain equivalent. Write under the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers/bounds, or non-finite required values fail clearly except for explicitly recoverable fields.

Mandatory output files:
- `players_clean.csv`
- `player_features.csv`
- `ranked_players.csv`
- `top_players_by_position.csv`
- `ranking_report.json`
