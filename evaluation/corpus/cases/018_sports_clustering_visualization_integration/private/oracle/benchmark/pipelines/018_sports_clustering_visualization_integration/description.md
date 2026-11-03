# Player clustering with three post-cluster views

Build `linear_to_fan_out`: validate players, derive production_index, fit standardized KMeans(k=4, seed 42, n_init=20, lloyd), then fan out to cluster profiles, team/cluster mix, and PCA plot data. Canonicalize labels by ascending standardized efficiency, usage, raw ID. Profiles contain counts and production/efficiency/usage means; team mix contains counts and within-team shares; plot data contains player, canonical cluster, PC1/PC2. No final join.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies. Alternative decomposition is acceptable only when logical tasks, checkpoints, and dependency semantics remain equivalent. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, and non-finite required values fail clearly.

Mandatory output files:
- `players_clean.csv`
- `cluster_features.csv`
- `player_clusters.csv`
- `cluster_model.pkl`
- `cluster_profiles.csv`
- `team_cluster_mix.csv`
- `cluster_plot_data.csv`
