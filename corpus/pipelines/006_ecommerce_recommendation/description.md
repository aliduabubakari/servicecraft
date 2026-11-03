# Deterministic in-stock product recommendation

Build a local Dagster pipeline that produces deterministic top-three product recommendations from purchase history and the product catalog. This is an offline ranking rule, not collaborative filtering or a claim of causal personalization quality.

Validate unique customer_id, product_id, and order_id keys. Every order customer and product must occur in its corresponding table. quantity must be finite and positive, rating finite and within [0,5], and in_stock binary.

Join orders to product category and sum purchased quantity by customer_id, product_id, and category. Write interactions.csv sorted by customer_id/product_id. For each customer/category, category_affinity is category purchased quantity divided by that customer's total purchased quantity. Product popularity is total purchased quantity divided by the maximum product total across the catalog, with zero for products never purchased.

For every customer, candidates are in-stock products they have never purchased. Score each candidate as 0.60*category_affinity + 0.25*normalized_popularity + 0.15*(rating/5). A category with no customer history has zero affinity. Rank by descending score and then ascending product_id. Emit at most three rows per customer with rank starting at one.

recommendations.csv contains customer_id, rank, product_id, product_name, category, and score. recommendation_report.json contains total customers, customers_with_recommendations, recommendation rows, top_k=3, and the count of in-stock catalog products. Do not use customer demographics or fixed recommendation lists.

Execution and output contract: generate executable Dagster code using only the supplied local files. Do not use network services, outputs from earlier runs, fixed analytical results, or human intervention. Each mandatory logical operation must be visible in the design/code. A different Dagster asset/op decomposition is allowed when it preserves the specified behavior, dependencies, and observable outputs. Write every output beneath the designated run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity. Missing required columns, broken identifier relationships, duplicate primary identifiers, invalid dates, and missing/non-finite required values must fail clearly.

Mandatory output files:
- `interactions.csv`
- `recommendations.csv`
- `recommendation_report.json`
