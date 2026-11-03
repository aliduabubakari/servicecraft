# Player-style clustering with convergent features and multiview diagnostics

Build a nine-task fan-in/fan-out pipeline. Validate and order players. Independently derive performance features (including production_index=points+assists+rebounds) and context features (including availability_rate=max(games-injury_games,0)/games); join one-to-one by player_id. Standardize nine declared features, fit KMeans with k=4, seed 42 and n_init=20, and canonicalize labels by increasing production, efficiency, then usage centroid. Fan assignments into cluster profiles, team-cluster composition, and cluster All-Star rates; reconverge those three artifacts into a reconciliation report. Every branch must consume the declared parent artifact.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `performance_features.csv`
- `context_features.csv`
- `model_features.csv`
- `cluster_assignments.csv`
- `cluster_profiles.csv`
- `team_cluster_mix.csv`
- `cluster_allstar_rates.csv`
- `cluster_report.json`
