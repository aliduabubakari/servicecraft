# Parallel delay classification and route service analysis

Build two disconnected three-task components. The delay component prepares declared predictors, uses a fixed stratified 75/25 seed-42 split, train-only scaling and one-hot encoding, LogisticRegression (C=1, liblinear), threshold 0.5, and five classification metrics. The service component independently prepares trip service fields, aggregates route delay/on-time/satisfaction plus service_score=(on_time+satisfaction/5)/2, and reports totals and the best route. Neither component consumes the other's artifacts.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `delay_model_data.csv`
- `delay_model.pkl`
- `delay_predictions.csv`
- `delay_metrics.json`
- `service_data.csv`
- `route_service.csv`
- `service_report.json`
