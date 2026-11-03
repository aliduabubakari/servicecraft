# Customer transaction aggregation and churn cohort analysis

Build a local Dagster pipeline for auditable customer-level transaction aggregation and churn cohort analysis. It describes historical associations; it does not train a churn predictor or prescribe retention actions.

Validate unique customer_id and transaction_id values and require every transaction customer_id to exist in customers.csv. is_churned and is_return must be binary. discount_applied is a nonnegative monetary amount. Parse transaction_date, require finite numeric measures, and define the analysis cutoff as the normalized maximum transaction date in the supplied data.

For each customer represented in transactions, compute transaction_count, total_spend (sum of amount, without changing the sign for returns), mean_order_value, total_items, return_count, returned_amount (sum amount where is_return=1), discounted_transaction_count (count where discount_applied is positive), total_discount (sum of discount_applied), last_transaction_date, return_rate, and days_since_last_transaction measured from the cutoff date. Sort customer_metrics.csv by customer_id.

Left-join these metrics to all customers one-to-one. Customers without transactions receive zero for numeric behavioral metrics and a blank last_transaction_date. Retain customer_id, segment, monthly_fee, support_contacts, is_churned, and the derived measures in customer_analysis.csv, sorted by customer_id.

Group the integrated customer table by segment. segment_summary.csv contains segment, customer_count, churn_rate, mean_total_spend, mean_transaction_count, and mean_days_since_last_transaction, sorted by segment. churn_report.json contains cutoff_date, customers, transactions, overall_churn_rate, total_spend, and segments. All values must be derived from the current inputs.

Execution and output contract: generate executable Dagster code using only the supplied local files. Do not use network services, outputs from earlier runs, fixed analytical results, or human intervention. Each mandatory logical operation must be visible in the design/code. A different Dagster asset/op decomposition is allowed when it preserves the specified behavior, dependencies, and observable outputs. Write every output beneath the designated run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity. Missing required columns, broken identifier relationships, duplicate primary identifiers, invalid dates, and missing/non-finite required values must fail clearly.

Mandatory output files:
- `customer_metrics.csv`
- `customer_analysis.csv`
- `segment_summary.csv`
- `churn_report.json`
