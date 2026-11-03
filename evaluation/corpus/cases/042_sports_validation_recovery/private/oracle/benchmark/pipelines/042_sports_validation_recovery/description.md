# Sports roster validation and deterministic recovery

Build a local Dagster pipeline that prepares a trustworthy sports roster and produces a data-derived quality report. This is a data validation and recovery task; it requires no predictive model or visualization.

Input `data.csv` contains player_id, team, position, games_played, points_per_game, minutes_per_game, and additional unused fields. Use the six named fields. Preserve the original one-based source row for audit. Strip whitespace from the three string fields; a whitespace-only string is missing. Replace missing team/position with the literal Unknown. Coerce invalid numeric text to missing values.

Reject rows with a missing player ID, a repeated normalized player ID after its first occurrence in input order, or games_played that is non-finite, non-integer, or outside [0,82]. For a row with several defects, use exactly one rejection reason in this priority: missing_player_id, duplicate_player_id, invalid_games_played. Duplicate detection uses the first input occurrence even if that occurrence is subsequently rejected.

On eligible rows, treat non-finite or negative points_per_game as missing. Treat non-finite minutes_per_game or values outside [0,48] as missing. Recover each field using the median of valid eligible values within the normalized position. If a group has no valid value, use the global median of valid eligible values for that field. If none exist globally, use zero. Compute all medians from the values before recovery. Do not change valid numeric values, cap outliers, or drop recoverable rows. Derive total_points = games_played * recovered points_per_game. Sort recovered rows lexicographically by player_id.

Produce the normalized, eligible, rejected, and recovered tables and the audit JSON files specified below. The final quality_report.json must contain input_rows, eligible_rows, rejected_rows, rejection_counts (nonzero reason counts), imputed_cells (counts for both recovered fields), players, total_points, and players_per_team. Counts must reconcile and report values must be computed from this execution's data. Reject records need source_row and reason so omissions are auditable. No timestamp or fixed recommendations are required.

Validation must precede recovery; the report must consume the recovered data and its recovery audit. Preserve intermediate artifacts so the evaluator can distinguish wrong eligibility, wrong recovery, and wrong reporting.

Execution and output contract: generate executable Dagster code using local files, without network access or external services. Each mandatory logical operation must be inspectable in the pipeline design/code. A different task decomposition is allowed if it preserves the stated behavior, dependencies, and observable intermediate outputs. Write outputs beneath the designated run output directory. Do not read outputs from previous runs. Preserve full numeric precision in CSV/JSON; numeric comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity; missing CSV values may use empty cells. Required JSON counts are integers. Files listed below are mandatory checkpoints and results, not prescriptions for the number of Dagster assets. Missing input columns fail clearly.

Mandatory output files:
- `normalized.csv` (required columns: source_row, player_id, team, position, games_played, points_per_game, minutes_per_game)
- `eligible.csv` (required columns: source_row, player_id, team, position, games_played, points_per_game, minutes_per_game)
- `rejected.csv` (required columns: source_row, player_id, reason)
- `validation.json`
- `recovered.csv` (required columns: source_row, player_id, team, position, games_played, points_per_game, minutes_per_game, total_points)
- `recovery.json`
- `quality_report.json`
