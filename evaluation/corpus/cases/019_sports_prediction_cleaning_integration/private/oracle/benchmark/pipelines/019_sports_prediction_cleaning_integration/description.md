# Prepared player data with three independent analytical leaves

Build a pure `fan_out` DAG. The root validates unique nonblank player_id, finite measures, and binary all_star; derives availability_rate=max(games_played-injury_games_missed,0)/games_played and salary_per_point=salary_millions/points_per_game (missing when points are zero); and emits players_clean.csv sorted by ID.

Three leaves consume only that table. Prediction leaf uses the ten declared numeric predictors, 75/25 stratified split seed 42, train-only StandardScaler, LogisticRegression(C=1, liblinear, max_iter=1000, seed 42), threshold 0.5, and outputs model/predictions plus accuracy, precision, recall, F1, ROC AUC. Availability leaf groups by team into player count and mean games, injury games, availability. Compensation leaf groups by position into player count and mean salary, points, and salary-per-point. Sort grouped outputs. Do not add a final join.

Execution contract: generate executable local Dagster code without networks, prior-run outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies; an alternative node decomposition is acceptable only when logical tasks, observable checkpoints, and dependency semantics remain equivalent. Write outputs below the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers, broken bounds, and non-finite required values fail clearly.

Mandatory output files:
- `players_clean.csv`
- `all_star_model.pkl`
- `all_star_predictions.csv`
- `all_star_metrics.json`
- `team_availability.csv`
- `position_compensation.csv`
