# Deterministic player-style clustering with canonical labels

Build a local Dagster pipeline that groups players by standardized performance and style measures, saves assignments, and profiles each group. It is descriptive clustering, not a prediction of player quality.

Require unique, nonblank player_id values and finite values for exactly these ordered clustering features: points_per_game, assists_per_game, rebounds_per_game, minutes_per_game, age, experience_years, salary_millions, play_style_score, efficiency_rating, usage_rate. Sort records by player_id before fitting. Retain team and position for output, but do not encode or cluster on them.

Fit StandardScaler (population variance) on all ordered feature rows. Fit KMeans with n_clusters=4, random_state=42, n_init=20, and algorithm=lloyd. Because raw cluster IDs are arbitrary, canonicalize them by sorting the standardized centroids ascending on efficiency_rating, then usage_rate, then raw cluster ID. Assign canonical IDs 0,1,2,3 in that order.

player_clusters.csv contains player_id, team, position, the ten feature values, and canonical cluster, sorted by player_id. cluster_profiles.csv contains canonical cluster, player_count, mean_points_per_game, mean_assists_per_game, mean_rebounds_per_game, mean_efficiency_rating, and mean_usage_rate, sorted by cluster. model.pkl stores the scaler, fitted model, feature order, and raw-to-canonical mapping.

clustering_report.json contains players, clusters=4, the ordered feature list, random_state=42, n_init=20, silhouette_score computed in standardized feature space using raw assignments, and cluster_sizes keyed by canonical cluster. All four clusters must be represented.

Execution and output contract: generate executable Dagster code using only the supplied local files. Do not use network services, outputs from earlier runs, fixed analytical results, or human intervention. Each mandatory logical operation must be visible in the design/code. A different Dagster asset/op decomposition is allowed when it preserves the specified behavior, dependencies, and observable outputs. Write every output beneath the designated run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity. Missing required columns, broken identifier relationships, duplicate primary identifiers, invalid dates, and missing/non-finite required values must fail clearly.

Mandatory output files:
- `player_clusters.csv`
- `cluster_profiles.csv`
- `model.pkl`
- `clustering_report.json`
