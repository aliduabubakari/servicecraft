# Parallel delay classification and geospatial route analysis

Build two disconnected three-task components. The prediction component prepares declared numeric and categorical fields, performs a fixed stratified 75/25 seed-42 split, fits train-only numeric scaling plus one-hot encoding and LogisticRegression (C=1, liblinear), applies threshold 0.5, and reports accuracy, precision, recall, F1, and ROC AUC. The geospatial component validates coordinate bounds, computes haversine distance using Earth radius 6371.0088 km and passenger-geodesic-km, aggregates routes, and reports totals. Neither component may consume artifacts from the other.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `delay_model_data.csv`
- `delay_model.pkl`
- `delay_predictions.csv`
- `delay_metrics.json`
- `trip_geography.csv`
- `route_geography.csv`
- `geography_report.json`
