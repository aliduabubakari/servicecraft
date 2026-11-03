"""Materialize the five reviewed batch-02 benchmark cases from upstream fixtures."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / "custom-pipelines"
REV = subprocess.check_output(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], text=True).strip()


def task(identifier, name, operation, inputs, outputs, requirements, parameters=None):
    return {"id": identifier, "name": name, "operation": operation, "required": True, "inputs": inputs, "outputs": outputs, "requirements": requirements, "parameters": parameters or {}}


def artifact(name, columns=None):
    return {"id": name, "path": name, "format": Path(name).suffix[1:], "required_columns": columns or []}


COMMON = """

Execution and output contract: generate executable Dagster code using only the supplied local files. Do not use network services, outputs from earlier runs, fixed analytical results, or human intervention. Each mandatory logical operation must be visible in the design/code. A different Dagster asset/op decomposition is allowed when it preserves the specified behavior, dependencies, and observable outputs. Write every output beneath the designated run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity. Missing required columns, broken identifier relationships, duplicate primary identifiers, invalid dates, and missing/non-finite required values must fail clearly.

Mandatory output files:
"""


CASES = {
"003_credit_risk": {
"title": "Credit-default classification with multi-source history aggregation", "domain": "finance", "family": "multisource_supervised_binary_classification",
"reason": "The upstream sixteen-step narrative mixes profiling, compliance, fairness, explainability, and several models without a single auditable target procedure.",
"sources": {"applications.csv": ("applications.csv", "csv"), "bureau_data.csv": ("bureau_data.xlsx", "xlsx"), "credit_history.csv": ("credit_history.json", "json")},
"input_columns": {"applications.csv": ["application_id","annual_income","loan_amount","dti_ratio","age","months_at_address","default_flag"], "bureau_data.csv": ["application_id","fico_score","total_accounts","delinquencies_2yrs","inquiries_6mo","public_records","revolving_utilization","credit_age_months"], "credit_history.csv": ["application_id","account_status","balance","utilization_pct"]},
"description": """Build a local Dagster pipeline that estimates default risk from three related sources using one fixed, reproducible classifier. This is an experimental benchmark, not a lending decision system, fairness audit, or regulatory-compliance claim.

Validate that application_id is unique in applications.csv and bureau_data.csv, both contain the same identifier set, and every credit_history.csv identifier occurs in applications.csv. The target default_flag must be 0 or 1. Use exactly the named columns; required numeric fields must be finite.

Aggregate credit history by application_id into history_record_count, history_mean_utilization_pct, history_max_balance, and history_current_account_count, where current means account_status equals the case-sensitive literal Current. Inner-join the application and bureau tables one-to-one, then left-join the history summary one-to-one. Sort integrated.csv by application_id.

Use every numeric column in integrated.csv except application_id and default_flag as the ordered predictors. Create a 75/25 stratified random split with random_state=42. Sort each resulting partition by application_id for output. Fit StandardScaler on training predictors only and LogisticRegression with C=1.0, solver=liblinear, max_iter=1000, random_state=42. Predict test probabilities and classify with probability >= 0.5.

predictions.csv must contain application_id, actual_default, default_probability, and predicted_default. fit_metadata.json records train/test rows, ordered features, split fraction, seed, and threshold. Compute accuracy, precision, recall, F1, and ROC AUC from the held-out predictions, with zero_division=0 for precision/recall/F1. metrics.json and credit_report.json contain metadata plus those computed metrics.""",
"artifacts": [artifact("integrated.csv", ["application_id","default_flag","history_record_count"]), artifact("train.csv", ["application_id","default_flag"]), artifact("test.csv", ["application_id","default_flag"]), artifact("model.pkl"), artifact("predictions.csv", ["application_id","actual_default","default_probability","predicted_default"]), artifact("fit_metadata.json"), artifact("metrics.json"), artifact("credit_report.json")],
"tasks": [
task("integrate", "Validate sources and aggregate account history", "multisource_validation_aggregation", ["input:applications.csv","input:bureau_data.csv","input:credit_history.csv"], ["integrated.csv"], ["Validate identifier relationships and numeric fields.", "Aggregate the four specified history measures and join sources with declared cardinalities."]),
task("split", "Create a reproducible stratified holdout", "stratified_split", ["integrated.csv"], ["train.csv","test.csv"], ["Use a 75/25 stratified split with seed 42 and preserve all rows."], {"test_fraction": 0.25, "random_state": 42}),
task("fit_predict", "Fit train-only scaling and logistic regression", "binary_classification", ["train.csv","test.csv"], ["model.pkl","predictions.csv","fit_metadata.json"], ["Fit preprocessing and estimator on training rows only.", "Emit probabilities and thresholded predictions for every test row."], {"estimator":"LogisticRegression","C":1.0,"solver":"liblinear","threshold":0.5}),
task("evaluate", "Measure held-out classification validity", "classification_evaluation", ["predictions.csv","fit_metadata.json"], ["metrics.json"], ["Compute accuracy, precision, recall, F1, and ROC AUC from held-out predictions."]),
task("report", "Publish credit experiment report", "model_report", ["metrics.json"], ["credit_report.json"], ["Publish the computed metrics and fit metadata without fixed results."])]},

"004_customer_churn": {
"title": "Customer transaction aggregation and churn cohort analysis", "domain": "finance", "family": "relational_aggregation_cohort_analysis",
"reason": "The upstream sixteen-step modeling playbook obscures a strong, directly testable relational aggregation problem and leaves model choice underspecified.",
"sources": {"customers.csv": ("customers.csv", "csv"), "transactions.csv": ("transactions.json", "json")},
"input_columns": {"customers.csv":["customer_id","segment","monthly_fee","support_contacts","is_churned"], "transactions.csv":["transaction_id","customer_id","transaction_date","amount","items_count","is_return","discount_applied"]},
"description": """Build a local Dagster pipeline for auditable customer-level transaction aggregation and churn cohort analysis. It describes historical associations; it does not train a churn predictor or prescribe retention actions.

Validate unique customer_id and transaction_id values and require every transaction customer_id to exist in customers.csv. is_churned and is_return must be binary. discount_applied is a nonnegative monetary amount. Parse transaction_date, require finite numeric measures, and define the analysis cutoff as the normalized maximum transaction date in the supplied data.

For each customer represented in transactions, compute transaction_count, total_spend (sum of amount, without changing the sign for returns), mean_order_value, total_items, return_count, returned_amount (sum amount where is_return=1), discounted_transaction_count (count where discount_applied is positive), total_discount (sum of discount_applied), last_transaction_date, return_rate, and days_since_last_transaction measured from the cutoff date. Sort customer_metrics.csv by customer_id.

Left-join these metrics to all customers one-to-one. Customers without transactions receive zero for numeric behavioral metrics and a blank last_transaction_date. Retain customer_id, segment, monthly_fee, support_contacts, is_churned, and the derived measures in customer_analysis.csv, sorted by customer_id.

Group the integrated customer table by segment. segment_summary.csv contains segment, customer_count, churn_rate, mean_total_spend, mean_transaction_count, and mean_days_since_last_transaction, sorted by segment. churn_report.json contains cutoff_date, customers, transactions, overall_churn_rate, total_spend, and segments. All values must be derived from the current inputs.""",
"artifacts": [artifact("customer_metrics.csv", ["customer_id","transaction_count","total_spend","discounted_transaction_count","total_discount","return_rate","days_since_last_transaction"]), artifact("customer_analysis.csv", ["customer_id","segment","is_churned","transaction_count","total_discount"]), artifact("segment_summary.csv", ["segment","customer_count","churn_rate","mean_total_spend","mean_transaction_count","mean_days_since_last_transaction"]), artifact("churn_report.json")],
"tasks": [
task("aggregate", "Validate and aggregate customer transactions", "relational_aggregation", ["input:customers.csv","input:transactions.csv"], ["customer_metrics.csv"], ["Validate identifier relationships, binary flags, dates, and numeric values.", "Compute the specified customer measures relative to the data-derived cutoff date."]),
task("integrate", "Integrate customer attributes and behavioral measures", "left_join", ["customer_metrics.csv","input:customers.csv"], ["customer_analysis.csv"], ["Left-join metrics to all supplied customers and apply the stated no-transaction defaults."], {"cardinality":"one_to_one"}),
task("summarize", "Summarize churn cohorts by segment", "grouped_aggregation", ["customer_analysis.csv"], ["segment_summary.csv"], ["Compute the five specified segment measures and sort deterministically."]),
task("report", "Publish churn cohort report", "aggregate_report", ["segment_summary.csv","input:customers.csv","input:transactions.csv"], ["churn_report.json"], ["Publish input-derived global counts, cutoff, churn rate, spend, and segment count."])]},

"005_demand_forecasting": {
"title": "Trailing-demand inventory reorder planning", "domain": "manufacturing", "family": "temporal_aggregation_inventory_optimization",
"reason": "The upstream forecasting narrative requests many incompatible model families while its actionable inventory formula and time window are not fixed.",
"sources": {"inventory.csv": ("inventory.csv", "csv"), "sales_orders.csv": ("sales_orders.json", "json"), "suppliers.csv": ("suppliers.xlsx", "xlsx")},
"input_columns": {"inventory.csv":["sku_id","product_name","supplier","lead_time_days","current_stock"], "sales_orders.csv":["order_id","sku_id","order_date","quantity"], "suppliers.csv":["supplier_name","minimum_order_qty"]},
"description": """Build a local Dagster pipeline that converts recent sales into deterministic SKU-level reorder recommendations. This is a trailing-demand inventory calculation, not a future-sales forecast or a learned model.

Validate unique sku_id, order_id, and supplier_name keys. Every sales SKU must occur in inventory.csv and every inventory supplier must occur in suppliers.csv. Parse order_date and require finite, nonnegative quantity, current_stock, lead_time_days, and minimum_order_qty; lead times and minimum quantities must be positive integers.

Let window_end be the normalized maximum order date and window_start be 89 days earlier, giving 90 inclusive calendar days. Sum quantity by SKU and calendar date within this window. Materialize all 90 dates for every inventory SKU, filling days without sales with zero. daily_demand.csv contains sku_id, date, and quantity sorted by SKU/date.

For each SKU compute mean_daily_demand and population standard deviation std_daily_demand (ddof=0), plus window_quantity. Join inventory and supplier information. Compute target_stock = mean_daily_demand * lead_time_days + 1.645 * std_daily_demand * sqrt(lead_time_days). Compute raw shortage as max(0, ceil(target_stock-current_stock)). If positive, round the shortage upward to an integer multiple of minimum_order_qty; otherwise recommend zero. reorder_required is 1 exactly when the recommendation is positive.

inventory_plan.csv contains the declared identifiers, source measures, demand statistics, target_stock, suggested_order_quantity, and reorder_required, sorted by sku_id. inventory_report.json contains the two window dates, window_days=90, service_z=1.645, SKU count, reorder SKU count, and total suggested units.""",
"artifacts": [artifact("daily_demand.csv", ["sku_id","date","quantity"]), artifact("inventory_plan.csv", ["sku_id","supplier","mean_daily_demand","std_daily_demand","target_stock","suggested_order_quantity","reorder_required"]), artifact("inventory_report.json")],
"tasks": [
task("aggregate", "Validate sources and construct zero-filled daily demand", "temporal_aggregation", ["input:inventory.csv","input:sales_orders.csv","input:suppliers.csv"], ["daily_demand.csv"], ["Validate primary/foreign keys and required values.", "Construct the inclusive trailing 90-day SKU/date grid and aggregate quantities."], {"window_days":90,"missing_day_quantity":0}),
task("plan", "Compute demand statistics and reorder quantities", "inventory_planning", ["daily_demand.csv","input:inventory.csv","input:suppliers.csv"], ["inventory_plan.csv"], ["Use population standard deviations, the declared service factor, lead time, stock, and MOQ rounding."], {"service_z":1.645,"std_ddof":0}),
task("report", "Publish inventory planning summary", "optimization_report", ["inventory_plan.csv"], ["inventory_report.json"], ["Publish data-derived window metadata, counts, and total suggested units."])]},

"006_ecommerce_recommendation": {
"title": "Deterministic in-stock product recommendation", "domain": "retail", "family": "relational_ranking_recommendation",
"reason": "The upstream recommendation pipeline clusters customer demographics and does not use order-product interactions to create recommendations.",
"sources": {"customers.csv": ("customers.csv", "csv"), "products.csv": ("products.csv", "csv"), "orders.csv": ("orders.json", "json")},
"input_columns": {"customers.csv":["customer_id"], "products.csv":["product_id","product_name","category","rating","in_stock"], "orders.csv":["order_id","customer_id","product_id","quantity"]},
"description": """Build a local Dagster pipeline that produces deterministic top-three product recommendations from purchase history and the product catalog. This is an offline ranking rule, not collaborative filtering or a claim of causal personalization quality.

Validate unique customer_id, product_id, and order_id keys. Every order customer and product must occur in its corresponding table. quantity must be finite and positive, rating finite and within [0,5], and in_stock binary.

Join orders to product category and sum purchased quantity by customer_id, product_id, and category. Write interactions.csv sorted by customer_id/product_id. For each customer/category, category_affinity is category purchased quantity divided by that customer's total purchased quantity. Product popularity is total purchased quantity divided by the maximum product total across the catalog, with zero for products never purchased.

For every customer, candidates are in-stock products they have never purchased. Score each candidate as 0.60*category_affinity + 0.25*normalized_popularity + 0.15*(rating/5). A category with no customer history has zero affinity. Rank by descending score and then ascending product_id. Emit at most three rows per customer with rank starting at one.

recommendations.csv contains customer_id, rank, product_id, product_name, category, and score. recommendation_report.json contains total customers, customers_with_recommendations, recommendation rows, top_k=3, and the count of in-stock catalog products. Do not use customer demographics or fixed recommendation lists.""",
"artifacts": [artifact("interactions.csv", ["customer_id","product_id","category","purchased_quantity"]), artifact("recommendations.csv", ["customer_id","rank","product_id","product_name","category","score"]), artifact("recommendation_report.json")],
"tasks": [
task("interactions", "Validate sources and aggregate purchase interactions", "relational_aggregation", ["input:customers.csv","input:products.csv","input:orders.csv"], ["interactions.csv"], ["Validate identifiers, foreign keys, quantity, rating, and stock flags.", "Aggregate purchased quantity by customer, product, and category."]),
task("rank", "Score and rank unseen in-stock products", "deterministic_ranking", ["interactions.csv","input:customers.csv","input:products.csv"], ["recommendations.csv"], ["Compute category affinity, normalized product popularity, and the specified weighted score.", "Exclude purchased/out-of-stock products and apply the stated deterministic ties."], {"top_k":3,"weights":{"category_affinity":0.60,"popularity":0.25,"rating":0.15}}),
task("report", "Publish recommendation coverage summary", "ranking_report", ["recommendations.csv","input:customers.csv","input:products.csv"], ["recommendation_report.json"], ["Publish data-derived customer, recommendation, and inventory coverage counts."])]},

"014_sports_clustering_integration_validation": {
"title": "Deterministic player-style clustering with canonical labels", "domain": "sports", "family": "unsupervised_clustering_profiling",
"reason": "The upstream clustering pipeline does not save assignments or profiles, and raw K-means labels are unsuitable for exact automated comparison.",
"sources": {"data.csv": ("data.csv", "csv")},
"input_columns": {"data.csv":["player_id","team","position","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","play_style_score","efficiency_rating","usage_rate"]},
"description": """Build a local Dagster pipeline that groups players by standardized performance and style measures, saves assignments, and profiles each group. It is descriptive clustering, not a prediction of player quality.

Require unique, nonblank player_id values and finite values for exactly these ordered clustering features: points_per_game, assists_per_game, rebounds_per_game, minutes_per_game, age, experience_years, salary_millions, play_style_score, efficiency_rating, usage_rate. Sort records by player_id before fitting. Retain team and position for output, but do not encode or cluster on them.

Fit StandardScaler (population variance) on all ordered feature rows. Fit KMeans with n_clusters=4, random_state=42, n_init=20, and algorithm=lloyd. Because raw cluster IDs are arbitrary, canonicalize them by sorting the standardized centroids ascending on efficiency_rating, then usage_rate, then raw cluster ID. Assign canonical IDs 0,1,2,3 in that order.

player_clusters.csv contains player_id, team, position, the ten feature values, and canonical cluster, sorted by player_id. cluster_profiles.csv contains canonical cluster, player_count, mean_points_per_game, mean_assists_per_game, mean_rebounds_per_game, mean_efficiency_rating, and mean_usage_rate, sorted by cluster. model.pkl stores the scaler, fitted model, feature order, and raw-to-canonical mapping.

clustering_report.json contains players, clusters=4, the ordered feature list, random_state=42, n_init=20, silhouette_score computed in standardized feature space using raw assignments, and cluster_sizes keyed by canonical cluster. All four clusters must be represented.""",
"artifacts": [artifact("player_clusters.csv", ["player_id","team","position","cluster"]), artifact("cluster_profiles.csv", ["cluster","player_count","mean_points_per_game","mean_assists_per_game","mean_rebounds_per_game","mean_efficiency_rating","mean_usage_rate"]), artifact("model.pkl"), artifact("clustering_report.json")],
"tasks": [
task("cluster", "Validate, standardize, and cluster player records", "kmeans_clustering", ["input:data.csv"], ["player_clusters.csv","model.pkl"], ["Use only the ordered ten numeric features after deterministic player sorting.", "Fit the declared scaler/K-means procedure and canonicalize labels from centroids."], {"clusters":4,"random_state":42,"n_init":20,"algorithm":"lloyd"}),
task("profile", "Profile canonical player clusters", "cluster_profiling", ["player_clusters.csv","model.pkl"], ["cluster_profiles.csv"], ["Compute the six specified size/mean fields by canonical cluster."]),
task("report", "Publish clustering validity summary", "clustering_report", ["cluster_profiles.csv"], ["clustering_report.json"], ["Publish parameters, cluster sizes, feature order, and silhouette score from this execution."])]}
}

RUNNER_NAMES = {
    "003_credit_risk": "credit",
    "004_customer_churn": "churn",
    "005_demand_forecasting": "inventory",
    "006_ecommerce_recommendation": "recommend",
    "014_sports_clustering_integration_validation": "cluster",
}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def materialize_input(source, source_format, destination):
    if source_format == "csv":
        shutil.copyfile(source, destination)
    elif source_format == "xlsx":
        pd.read_excel(source).to_csv(destination, index=False)
    elif source_format == "json":
        pd.read_json(source).to_csv(destination, index=False)
    else:
        raise ValueError(source_format)


def main():
    reference = (ROOT / "tools" / "batch02_reference.py").read_text()
    batch = []
    for name, case in CASES.items():
        destination = ROOT / "pipelines" / name
        inputs_dir = destination / "inputs"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        conversions = []
        for output_name, (source_name, source_format) in case["sources"].items():
            source = UPSTREAM / name / "data" / source_name
            materialize_input(source, source_format, inputs_dir / output_name)
            conversions.append({"source": source_name, "benchmark_file": output_name, "conversion": f"{source_format}_to_csv" if source_format != "csv" else "byte_copy"})
        inputs = [{"id": "input:" + filename, "path": "inputs/" + filename, "format": "csv", "required_columns": columns} for filename, columns in case["input_columns"].items()]
        producers = {output: item["id"] for item in case["tasks"] for output in item["outputs"]}
        dependencies = []
        for item in case["tasks"]:
            for parent in sorted({producers[value] for value in item["inputs"] if value in producers}):
                dependencies.append({"source": parent, "target": item["id"], "kind": "data", "artifacts": [value for value in item["inputs"] if producers.get(value) == parent]})
        graph = {"schema_version":"inlumen.benchmark.task-graph@2", "pipeline_id":name, "benchmark_revision":"batch-02", "review_status":"author_review_pending", "title":case["title"], "domain":case["domain"], "family_id":case["family"], "topology":"linear", "inputs":inputs, "tasks":case["tasks"], "artifacts":case["artifacts"], "dependencies":dependencies, "rq1_policy":{"task_matching":"reviewed_semantic_mapping","allow_split_or_merge":True,"exact_node_count_required":False,"data_edges_require_artifact_binding":True,"unknown_semantics":"unassessed_not_pass"}, "reference":{"entrypoint":"reference.py","task_functions":{item["id"]:RUNNER_NAMES[name] for item in case["tasks"]}}, "numeric_tolerance":{"atol":1e-6,"rtol":1e-6}}
        outputs = "\n".join(f"- `{item['path']}`" for item in case["artifacts"])
        (destination / "description.md").write_text(f"# {case['title']}\n\n{case['description'].strip()}{COMMON}{outputs}\n")
        save(destination / "task_graph.json", graph)
        (destination / "reference.py").write_text(reference)
        (destination / "requirements.txt").write_text("numpy==2.0.1\npandas==2.2.2\nscikit-learn==1.5.1\nopenpyxl==3.1.5\n")
        hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(inputs_dir.iterdir())}
        save(destination / "provenance.json", {"upstream_repository":"https://github.com/aliduabubakari/custom-pipelines", "upstream_commit":REV, "upstream_pipeline":name, "selection_reason":case["reason"], "input_transformations":conversions, "pilot_input_sha256":hashes, "description_status":"behaviorally_rewritten_for_evaluation", "review_status":"author_review_pending"})
        batch.append({"pipeline_id":name,"title":case["title"],"domain":case["domain"],"family_id":case["family"],"topology":"linear","task_count":len(case["tasks"]),"review_status":"author_review_pending"})
    save(ROOT / "batch-02.json", {"batch_id":"batch-02","case_count":len(batch),"purpose":"Second five-case qualification batch spanning classification, aggregation, planning, ranking, and clustering.","cases":batch})
    print(f"Prepared {len(batch)} cases at upstream revision {REV}")


if __name__ == "__main__":
    main()
