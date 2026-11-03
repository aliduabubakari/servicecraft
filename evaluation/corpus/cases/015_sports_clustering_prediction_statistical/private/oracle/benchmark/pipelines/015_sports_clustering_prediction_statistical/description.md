# Independent player clustering and All-Star prediction

Build two disconnected three-task components (`parallel` topology) over the player input. Both validate unique nonblank player_id and finite required values, but neither may consume artifacts from the other.

Clustering component prepares player/team/position and exactly seven ordered style/performance features. Fit StandardScaler and KMeans(k=4, seed 42, n_init=20, lloyd). Canonicalize raw labels by ascending standardized centroid efficiency_rating, then usage_rate, then raw ID. Emit assignments/model, then profiles with cluster size and mean points/assists/rebounds/efficiency/usage plus a report containing player count, k, and silhouette score.

Prediction component prepares all_star plus the fourteen declared numeric predictors. Use a 75/25 stratified split with seed 42, train-only StandardScaler, LogisticRegression(C=1, liblinear, max_iter=1000, seed 42), and threshold 0.5. Emit model and held-out predictions, then accuracy, precision, recall, F1, and ROC AUC. No cluster label or clustering artifact may be used by prediction.

Execution contract: generate executable local Dagster code without network services, prior-run outputs, fixed analytical answers, or human intervention. The declared topology is a scored semantic property: preserve independent branches and every artifact-backed join. Alternative Dagster decomposition is allowed only when logical requirements, dependencies, topology, and observable checkpoints remain equivalent. Write outputs beneath the run output directory. Preserve numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid identifiers/dates, broken relationships, and non-finite required values must fail clearly.

Mandatory output files:
- `clustering_features.csv`
- `player_clusters.csv`
- `cluster_model.pkl`
- `cluster_profiles.csv`
- `cluster_report.json`
- `prediction_features.csv`
- `all_star_model.pkl`
- `all_star_predictions.csv`
- `all_star_metrics.json`
