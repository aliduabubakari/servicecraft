# Transportation economics with convergent feature branches

Build a `fan_in_fan_out` trip-economics DAG. Validate unique trip_id, finite nonnegative measures, and emit trips_clean.csv. It fans out into revenue features (revenue_per_passenger and revenue minus fare*passengers) and cost features (cost_per_km and cost_per_delay_minute, zero for zero delay). Join branches one-to-one with clean trips, derive profit=revenue-cost and profit_margin=profit/revenue, and emit trip_economics.csv.

The integrated table fans out to a profit regression and route profitability summary. Regression uses ten ordered predictors, 80/20 split seed 42, train-only StandardScaler and LinearRegression; emits model/predictions and MAE/RMSE/R2 metrics. Route summary emits counts, total revenue/cost/profit and mean margin. economics_report.json reconverges metrics and summary, publishes global totals and most profitable route with route ascending tie-break.

Execution contract: generate executable local Dagster code without networks, prior-run outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies; an alternative node decomposition is acceptable only when logical tasks, observable checkpoints, and dependency semantics remain equivalent. Write outputs below the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers, broken bounds, and non-finite required values fail clearly.

Mandatory output files:
- `trips_clean.csv`
- `revenue_features.csv`
- `cost_features.csv`
- `trip_economics.csv`
- `profit_model.pkl`
- `profit_predictions.csv`
- `profit_metrics.json`
- `route_profitability.csv`
- `economics_report.json`
