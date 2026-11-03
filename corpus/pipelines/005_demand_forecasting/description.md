# Trailing-demand inventory reorder planning

Build a local Dagster pipeline that converts recent sales into deterministic SKU-level reorder recommendations. This is a trailing-demand inventory calculation, not a future-sales forecast or a learned model.

Validate unique sku_id, order_id, and supplier_name keys. Every sales SKU must occur in inventory.csv and every inventory supplier must occur in suppliers.csv. Parse order_date and require finite, nonnegative quantity, current_stock, lead_time_days, and minimum_order_qty; lead times and minimum quantities must be positive integers.

Let window_end be the normalized maximum order date and window_start be 89 days earlier, giving 90 inclusive calendar days. Sum quantity by SKU and calendar date within this window. Materialize all 90 dates for every inventory SKU, filling days without sales with zero. daily_demand.csv contains sku_id, date, and quantity sorted by SKU/date.

For each SKU compute mean_daily_demand and population standard deviation std_daily_demand (ddof=0), plus window_quantity. Join inventory and supplier information. Compute target_stock = mean_daily_demand * lead_time_days + 1.645 * std_daily_demand * sqrt(lead_time_days). Compute raw shortage as max(0, ceil(target_stock-current_stock)). If positive, round the shortage upward to an integer multiple of minimum_order_qty; otherwise recommend zero. reorder_required is 1 exactly when the recommendation is positive.

inventory_plan.csv contains the declared identifiers, source measures, demand statistics, target_stock, suggested_order_quantity, and reorder_required, sorted by sku_id. inventory_report.json contains the two window dates, window_days=90, service_z=1.645, SKU count, reorder SKU count, and total suggested units.

Execution and output contract: generate executable Dagster code using only the supplied local files. Do not use network services, outputs from earlier runs, fixed analytical results, or human intervention. Each mandatory logical operation must be visible in the design/code. A different Dagster asset/op decomposition is allowed when it preserves the specified behavior, dependencies, and observable outputs. Write every output beneath the designated run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity. Missing required columns, broken identifier relationships, duplicate primary identifiers, invalid dates, and missing/non-finite required values must fail clearly.

Mandatory output files:
- `daily_demand.csv`
- `inventory_plan.csv`
- `inventory_report.json`
