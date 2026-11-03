# Trip clustering with independent post-cluster validation views

Build a `linear_to_fan_out` DAG: validate trips, prepare clustering features, fit clusters, then fan out to three leaves. Require unique nonblank trip_id, finite numeric measures, and binary holiday/peak flags. Use ordered features departure_hour, distance_km, passengers, fare_amount, delay_minutes, is_holiday, peak_hour, avg_load_factor.

Fit StandardScaler and KMeans(k=5, seed 42, n_init=20, lloyd). Canonicalize labels by ascending standardized avg_load_factor, then delay_minutes, then raw ID. trip_clusters.csv retains all prepared fields with the canonical assignment. Profile leaf outputs count and mean distance/passengers/delay/load per cluster. Route-mix leaf outputs trip_count and within-route share by route/cluster. Validation leaf outputs trips, k, silhouette, inertia, and canonical cluster sizes. All leaves consume only artifacts produced by the cluster task; none rereads earlier stages or depends on another leaf.

Execution contract: generate executable local Dagster code without networks, prior-run outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies; an alternative node decomposition is acceptable only when logical tasks, observable checkpoints, and dependency semantics remain equivalent. Write outputs below the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers, broken bounds, and non-finite required values fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `clustering_features.csv`
- `trip_clusters.csv`
- `cluster_model.pkl`
- `cluster_profiles.csv`
- `route_cluster_mix.csv`
- `cluster_validation.json`
