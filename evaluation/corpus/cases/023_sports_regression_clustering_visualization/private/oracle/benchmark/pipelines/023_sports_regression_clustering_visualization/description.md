# Independent market-value regression and player clustering

Build two disconnected three-task components. Regression component validates players and prepares market_value with eleven ordered numeric predictors; uses an 80/20 random split seed 42, train-only StandardScaler and LinearRegression; emits model/predictions then MAE, RMSE, R2 metrics.

Clustering component independently prepares team/position and six ordered style features; applies StandardScaler and KMeans(k=4, seed 42, n_init=20, lloyd); canonicalizes labels by ascending standardized efficiency_rating, then usage_rate, then raw ID; emits assignments/model then cluster profiles and silhouette report. No regression artifact may feed clustering and no cluster artifact may feed regression.

Execution contract: generate executable local Dagster code without networks, prior-run outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies; an alternative node decomposition is acceptable only when logical tasks, observable checkpoints, and dependency semantics remain equivalent. Write outputs below the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers, broken bounds, and non-finite required values fail clearly.

Mandatory output files:
- `regression_features.csv`
- `market_value_model.pkl`
- `market_value_predictions.csv`
- `market_value_metrics.json`
- `clustering_features.csv`
- `player_clusters.csv`
- `cluster_model.pkl`
- `cluster_profiles.csv`
- `cluster_report.json`
