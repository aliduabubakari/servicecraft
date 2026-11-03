"""Trusted deterministic references for benchmark batch 02.

This file is copied into each case as reference.py by prepare_batch02.py.
"""
import argparse
import json
import math
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def require(frame, columns, name):
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")
    if frame.empty:
        raise ValueError(f"{name} is empty")


def finite(frame, columns, name):
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if not np.isfinite(frame[columns].to_numpy(float)).all():
        raise ValueError(f"{name} contains missing or non-finite numeric values")


def credit(data, out):
    apps = pd.read_csv(data / "applications.csv")
    bureau = pd.read_csv(data / "bureau_data.csv")
    history = pd.read_csv(data / "credit_history.csv")
    ac = ["application_id", "annual_income", "loan_amount", "dti_ratio", "age", "months_at_address", "default_flag"]
    bc = ["application_id", "fico_score", "total_accounts", "delinquencies_2yrs", "inquiries_6mo", "public_records", "revolving_utilization", "credit_age_months"]
    hc = ["application_id", "account_status", "balance", "utilization_pct"]
    require(apps, ac, "applications.csv"); require(bureau, bc, "bureau_data.csv"); require(history, hc, "credit_history.csv")
    if not apps.application_id.is_unique or not bureau.application_id.is_unique or apps.application_id.astype(str).str.strip().eq("").any() or bureau.application_id.astype(str).str.strip().eq("").any():
        raise ValueError("application_id must be unique in application and bureau sources")
    if set(apps.application_id) != set(bureau.application_id) or not set(history.application_id) <= set(apps.application_id):
        raise ValueError("application source keys do not reconcile")
    finite(apps, ac[1:], "applications.csv"); finite(bureau, bc[1:], "bureau_data.csv"); finite(history, ["balance", "utilization_pct"], "credit_history.csv")
    if not set(apps.default_flag.unique()) <= {0, 1}:
        raise ValueError("default_flag must be binary")
    history = history.assign(is_current=(history.account_status == "Current").astype(int))
    summary = history.groupby("application_id", as_index=False).agg(
        history_record_count=("account_status", "size"),
        history_mean_utilization_pct=("utilization_pct", "mean"),
        history_max_balance=("balance", "max"),
        history_current_account_count=("is_current", "sum"),
    )
    integrated = apps[ac].merge(bureau[bc], on="application_id", validate="one_to_one").merge(summary, on="application_id", how="left", validate="one_to_one")
    integrated = integrated.sort_values("application_id").reset_index(drop=True)
    integrated.to_csv(out / "integrated.csv", index=False)
    features = [c for c in integrated.columns if c not in {"application_id", "default_flag"}]
    train, test = train_test_split(integrated, test_size=0.25, random_state=42, stratify=integrated.default_flag)
    train = train.sort_values("application_id").reset_index(drop=True); test = test.sort_values("application_id").reset_index(drop=True)
    train.to_csv(out / "train.csv", index=False); test.to_csv(out / "test.csv", index=False)
    model = Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(C=1.0, solver="liblinear", max_iter=1000, random_state=42))])
    model.fit(train[features], train.default_flag)
    probability = model.predict_proba(test[features])[:, 1]
    predicted = (probability >= 0.5).astype(int)
    predictions = pd.DataFrame({"application_id": test.application_id, "actual_default": test.default_flag, "default_probability": probability, "predicted_default": predicted})
    predictions.to_csv(out / "predictions.csv", index=False)
    with (out / "model.pkl").open("wb") as handle: pickle.dump(model, handle)
    metadata = {"train_rows": len(train), "test_rows": len(test), "features": features, "test_fraction": 0.25, "random_state": 42, "threshold": 0.5}
    write_json(out / "fit_metadata.json", metadata)
    metrics = {**metadata, "accuracy": accuracy_score(test.default_flag, predicted), "precision": precision_score(test.default_flag, predicted, zero_division=0), "recall": recall_score(test.default_flag, predicted, zero_division=0), "f1": f1_score(test.default_flag, predicted, zero_division=0), "roc_auc": roc_auc_score(test.default_flag, probability)}
    write_json(out / "metrics.json", metrics); write_json(out / "credit_report.json", metrics)


def churn(data, out):
    customers = pd.read_csv(data / "customers.csv")
    transactions = pd.read_csv(data / "transactions.csv")
    cc = ["customer_id", "segment", "monthly_fee", "support_contacts", "is_churned"]
    tc = ["transaction_id", "customer_id", "transaction_date", "amount", "items_count", "is_return", "discount_applied"]
    require(customers, cc, "customers.csv"); require(transactions, tc, "transactions.csv")
    if not customers.customer_id.is_unique or not transactions.transaction_id.is_unique or customers.customer_id.astype(str).str.strip().eq("").any() or transactions.transaction_id.astype(str).str.strip().eq("").any() or not set(transactions.customer_id) <= set(customers.customer_id):
        raise ValueError("customer or transaction keys do not reconcile")
    finite(customers, ["monthly_fee", "support_contacts", "is_churned"], "customers.csv")
    finite(transactions, ["amount", "items_count", "is_return", "discount_applied"], "transactions.csv")
    if not set(customers.is_churned.unique()) <= {0, 1} or not set(transactions.is_return.unique()) <= {0, 1}:
        raise ValueError("churn and return flags must be binary")
    if (transactions.discount_applied < 0).any():
        raise ValueError("discount_applied must be nonnegative")
    transactions["transaction_date"] = pd.to_datetime(transactions.transaction_date, errors="raise")
    cutoff = transactions.transaction_date.max().normalize()
    transactions["return_amount"] = np.where(transactions.is_return == 1, transactions.amount, 0.0)
    transactions["is_discounted"] = (transactions.discount_applied > 0).astype(int)
    aggregate = transactions.groupby("customer_id", as_index=False).agg(
        transaction_count=("transaction_id", "size"), total_spend=("amount", "sum"), mean_order_value=("amount", "mean"),
        total_items=("items_count", "sum"), return_count=("is_return", "sum"), returned_amount=("return_amount", "sum"),
        discounted_transaction_count=("is_discounted", "sum"), total_discount=("discount_applied", "sum"), last_transaction_date=("transaction_date", "max"),
    )
    aggregate["return_rate"] = aggregate.return_count / aggregate.transaction_count
    aggregate["days_since_last_transaction"] = (cutoff - aggregate.last_transaction_date.dt.normalize()).dt.days
    aggregate.last_transaction_date = aggregate.last_transaction_date.dt.strftime("%Y-%m-%d")
    aggregate = aggregate.sort_values("customer_id").reset_index(drop=True)
    aggregate.to_csv(out / "customer_metrics.csv", index=False)
    integrated = customers[cc].merge(aggregate, on="customer_id", how="left", validate="one_to_one")
    numeric = ["transaction_count", "total_spend", "mean_order_value", "total_items", "return_count", "returned_amount", "discounted_transaction_count", "total_discount", "return_rate", "days_since_last_transaction"]
    integrated[numeric] = integrated[numeric].fillna(0)
    integrated["last_transaction_date"] = integrated.last_transaction_date.fillna("")
    integrated = integrated.sort_values("customer_id").reset_index(drop=True)
    integrated.to_csv(out / "customer_analysis.csv", index=False)
    cohort = integrated.groupby("segment", as_index=False).agg(customer_count=("customer_id", "size"), churn_rate=("is_churned", "mean"), mean_total_spend=("total_spend", "mean"), mean_transaction_count=("transaction_count", "mean"), mean_days_since_last_transaction=("days_since_last_transaction", "mean")).sort_values("segment")
    cohort.to_csv(out / "segment_summary.csv", index=False)
    report = {"cutoff_date": cutoff.strftime("%Y-%m-%d"), "customers": len(integrated), "transactions": len(transactions), "overall_churn_rate": integrated.is_churned.mean(), "total_spend": integrated.total_spend.sum(), "segments": len(cohort)}
    write_json(out / "churn_report.json", report)


def inventory(data, out):
    inventory = pd.read_csv(data / "inventory.csv")
    sales = pd.read_csv(data / "sales_orders.csv")
    suppliers = pd.read_csv(data / "suppliers.csv")
    ic = ["sku_id", "product_name", "supplier", "lead_time_days", "current_stock"]
    sc = ["order_id", "sku_id", "order_date", "quantity"]
    uc = ["supplier_name", "minimum_order_qty"]
    require(inventory, ic, "inventory.csv"); require(sales, sc, "sales_orders.csv"); require(suppliers, uc, "suppliers.csv")
    if not inventory.sku_id.is_unique or not sales.order_id.is_unique or not suppliers.supplier_name.is_unique or inventory.sku_id.astype(str).str.strip().eq("").any() or sales.order_id.astype(str).str.strip().eq("").any():
        raise ValueError("inventory, order, and supplier identifiers must be unique")
    if not set(sales.sku_id) <= set(inventory.sku_id) or not set(inventory.supplier) <= set(suppliers.supplier_name):
        raise ValueError("sales and supplier keys do not reconcile")
    finite(inventory, ["lead_time_days", "current_stock"], "inventory.csv"); finite(sales, ["quantity"], "sales_orders.csv"); finite(suppliers, ["minimum_order_qty"], "suppliers.csv")
    if (inventory[["lead_time_days", "current_stock"]].to_numpy() < 0).any() or (sales.quantity < 0).any() or (suppliers.minimum_order_qty <= 0).any():
        raise ValueError("inventory planning measures violate nonnegative/positive bounds")
    if not inventory.lead_time_days.map(lambda value: float(value).is_integer()).all() or not suppliers.minimum_order_qty.map(lambda value: float(value).is_integer()).all():
        raise ValueError("lead_time_days and minimum_order_qty must be integers")
    sales["order_date"] = pd.to_datetime(sales.order_date, errors="raise")
    end = sales.order_date.max().normalize(); start = end - pd.Timedelta(days=89)
    recent = sales[(sales.order_date.dt.normalize() >= start) & (sales.order_date.dt.normalize() <= end)].copy()
    recent["date"] = recent.order_date.dt.normalize()
    daily = recent.groupby(["sku_id", "date"], as_index=False).quantity.sum()
    grid = pd.MultiIndex.from_product([sorted(inventory.sku_id), pd.date_range(start, end)], names=["sku_id", "date"]).to_frame(index=False)
    daily = grid.merge(daily, on=["sku_id", "date"], how="left").fillna({"quantity": 0}).sort_values(["sku_id", "date"])
    daily.to_csv(out / "daily_demand.csv", index=False, date_format="%Y-%m-%d")
    demand = daily.groupby("sku_id", as_index=False).agg(mean_daily_demand=("quantity", "mean"), std_daily_demand=("quantity", lambda x: x.std(ddof=0)), window_quantity=("quantity", "sum"))
    plan = inventory[ic].merge(demand, on="sku_id", validate="one_to_one").merge(suppliers[uc], left_on="supplier", right_on="supplier_name", validate="many_to_one")
    plan["target_stock"] = plan.mean_daily_demand * plan.lead_time_days + 1.645 * plan.std_daily_demand * np.sqrt(plan.lead_time_days)
    raw = np.maximum(0, np.ceil(plan.target_stock - plan.current_stock)).astype(int)
    moq = plan.minimum_order_qty.astype(int)
    plan["suggested_order_quantity"] = np.where(raw > 0, np.ceil(raw / moq).astype(int) * moq, 0)
    plan["reorder_required"] = (plan.suggested_order_quantity > 0).astype(int)
    columns = ["sku_id", "product_name", "supplier", "lead_time_days", "current_stock", "minimum_order_qty", "mean_daily_demand", "std_daily_demand", "window_quantity", "target_stock", "suggested_order_quantity", "reorder_required"]
    plan = plan[columns].sort_values("sku_id").reset_index(drop=True)
    plan.to_csv(out / "inventory_plan.csv", index=False)
    report = {"window_start": start.strftime("%Y-%m-%d"), "window_end": end.strftime("%Y-%m-%d"), "window_days": 90, "service_z": 1.645, "skus": len(plan), "reorder_skus": int(plan.reorder_required.sum()), "total_suggested_units": int(plan.suggested_order_quantity.sum())}
    write_json(out / "inventory_report.json", report)


def recommend(data, out):
    customers = pd.read_csv(data / "customers.csv"); products = pd.read_csv(data / "products.csv"); orders = pd.read_csv(data / "orders.csv")
    cc = ["customer_id"]; pc = ["product_id", "product_name", "category", "rating", "in_stock"]; oc = ["order_id", "customer_id", "product_id", "quantity"]
    require(customers, cc, "customers.csv"); require(products, pc, "products.csv"); require(orders, oc, "orders.csv")
    if not customers.customer_id.is_unique or not products.product_id.is_unique or not orders.order_id.is_unique or customers.customer_id.astype(str).str.strip().eq("").any() or products.product_id.astype(str).str.strip().eq("").any() or orders.order_id.astype(str).str.strip().eq("").any():
        raise ValueError("customer, product, and order identifiers must be unique")
    if not set(orders.customer_id) <= set(customers.customer_id) or not set(orders.product_id) <= set(products.product_id):
        raise ValueError("order keys do not reconcile")
    finite(products, ["rating", "in_stock"], "products.csv"); finite(orders, ["quantity"], "orders.csv")
    if (orders.quantity <= 0).any() or not products.rating.between(0, 5).all() or not set(products.in_stock.unique()) <= {0, 1}:
        raise ValueError("quantity, rating, or stock flag violates its declared bounds")
    interactions = orders.merge(products[["product_id", "category"]], on="product_id", validate="many_to_one").groupby(["customer_id", "product_id", "category"], as_index=False).quantity.sum()
    interactions = interactions.rename(columns={"quantity": "purchased_quantity"}).sort_values(["customer_id", "product_id"])
    interactions.to_csv(out / "interactions.csv", index=False)
    category = interactions.groupby(["customer_id", "category"], as_index=False).purchased_quantity.sum()
    totals = category.groupby("customer_id").purchased_quantity.transform("sum")
    category["category_affinity"] = category.purchased_quantity / totals
    affinity = {(r.customer_id, r.category): r.category_affinity for r in category.itertuples()}
    popularity = interactions.groupby("product_id").purchased_quantity.sum().reindex(products.product_id, fill_value=0)
    max_pop = float(popularity.max()) or 1.0
    pop = (popularity / max_pop).to_dict()
    purchased = interactions.groupby("customer_id").product_id.apply(set).to_dict()
    available = products[products.in_stock == 1]
    rows = []
    for customer_id in sorted(customers.customer_id):
        candidates = []
        for p in available.itertuples():
            if p.product_id in purchased.get(customer_id, set()): continue
            score = 0.60 * affinity.get((customer_id, p.category), 0.0) + 0.25 * pop[p.product_id] + 0.15 * (p.rating / 5.0)
            candidates.append((score, p.product_id, p.product_name, p.category))
        for rank, (score, product_id, product_name, cat) in enumerate(sorted(candidates, key=lambda x: (-x[0], x[1]))[:3], 1):
            rows.append([customer_id, rank, product_id, product_name, cat, score])
    recs = pd.DataFrame(rows, columns=["customer_id", "rank", "product_id", "product_name", "category", "score"])
    recs.to_csv(out / "recommendations.csv", index=False)
    report = {"customers": len(customers), "customers_with_recommendations": int(recs.customer_id.nunique()), "recommendations": len(recs), "top_k": 3, "in_stock_products": int((products.in_stock == 1).sum())}
    write_json(out / "recommendation_report.json", report)


def cluster(data, out):
    players = pd.read_csv(data / "data.csv")
    features = ["points_per_game", "assists_per_game", "rebounds_per_game", "minutes_per_game", "age", "experience_years", "salary_millions", "play_style_score", "efficiency_rating", "usage_rate"]
    require(players, ["player_id", "team", "position", *features], "data.csv")
    if not players.player_id.is_unique or players.player_id.astype(str).str.strip().eq("").any(): raise ValueError("player_id must be unique and nonblank")
    finite(players, features, "data.csv")
    ordered = players.sort_values("player_id").reset_index(drop=True)
    scaler = StandardScaler(); x = scaler.fit_transform(ordered[features])
    model = KMeans(n_clusters=4, random_state=42, n_init=20, algorithm="lloyd").fit(x)
    raw = model.labels_
    ranking = pd.DataFrame({"raw": range(4), "efficiency": model.cluster_centers_[:, features.index("efficiency_rating")], "usage": model.cluster_centers_[:, features.index("usage_rate")]}).sort_values(["efficiency", "usage", "raw"])
    mapping = {int(raw_id): int(canonical) for canonical, raw_id in enumerate(ranking.raw)}
    result = ordered[["player_id", "team", "position", *features]].copy(); result["cluster"] = [mapping[int(v)] for v in raw]
    result.to_csv(out / "player_clusters.csv", index=False)
    profile = result.groupby("cluster", as_index=False).agg(player_count=("player_id", "size"), mean_points_per_game=("points_per_game", "mean"), mean_assists_per_game=("assists_per_game", "mean"), mean_rebounds_per_game=("rebounds_per_game", "mean"), mean_efficiency_rating=("efficiency_rating", "mean"), mean_usage_rate=("usage_rate", "mean")).sort_values("cluster")
    profile.to_csv(out / "cluster_profiles.csv", index=False)
    with (out / "model.pkl").open("wb") as handle: pickle.dump({"scaler": scaler, "model": model, "canonical_mapping": mapping, "features": features}, handle)
    report = {"players": len(result), "clusters": 4, "features": features, "random_state": 42, "n_init": 20, "silhouette_score": silhouette_score(x, raw), "cluster_sizes": {str(int(r.cluster)): int(r.player_count) for r in profile.itertuples()}}
    write_json(out / "clustering_report.json", report)


RUNNERS = {
    "003_credit_risk": credit,
    "004_customer_churn": churn,
    "005_demand_forecasting": inventory,
    "006_ecommerce_recommendation": recommend,
    "014_sports_clustering_integration_validation": cluster,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--data-dir", type=Path, required=True); parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    RUNNERS[Path(__file__).resolve().parent.name](args.data_dir, args.output_dir)
