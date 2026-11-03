# Convergent player-style features with multi-view cluster analysis

Build a 9-task `fan_in_fan_out` DAG. Validate unique players and finite fields. players_clean.csv fans out to shooting features (three percentages plus their row mean) and playmaking features (points/assists/rebounds/style/efficiency/usage plus production_index). Join one-to-one into style_features.csv.

Scale the ten ordered derived/source features and fit KMeans(k=5, seed 42, n_init=20, lloyd). Canonicalize labels by ascending standardized efficiency_rating, usage_rate, raw ID. The cluster task fans out to: cluster profiles; position/cluster counts and within-position shares; and PCA two-component scatter data. A final report consumes all three, reporting players, k, silhouette, positions, and scatter rows.

Execution contract: generate executable local Dagster code without network access, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology; alternative node decomposition is allowed only when logical operations, checkpoints, and dependency semantics remain equivalent. Write under the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers/bounds, or non-finite required values fail clearly except for explicitly recoverable fields.

Mandatory output files:
- `players_clean.csv`
- `shooting_features.csv`
- `playmaking_features.csv`
- `style_features.csv`
- `player_clusters.csv`
- `cluster_model.pkl`
- `cluster_profiles.csv`
- `position_cluster_mix.csv`
- `cluster_scatter_data.csv`
- `style_report.json`
