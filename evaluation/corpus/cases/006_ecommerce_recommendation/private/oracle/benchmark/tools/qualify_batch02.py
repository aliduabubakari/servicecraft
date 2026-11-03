"""Qualify batch-02 references, invariants, failure behavior, and exports."""
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from export_inputs import export
from validate_specs import ROOT, validate

CASES = ["003_credit_risk", "004_customer_churn", "005_demand_forecasting", "006_ecommerce_recommendation", "014_sports_clustering_integration_validation"]


def load(path):
    def reject(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(path.read_text(), parse_constant=reject)


def run(case, data, output, expect_failure=False):
    output.mkdir()
    command = [sys.executable, str(ROOT / "pipelines" / case / "reference.py"), "--data-dir", str(data), "--output-dir", str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    if expect_failure:
        assert result.returncode != 0, f"{case} accepted invalid fixture"
        return
    if result.returncode:
        raise RuntimeError(result.stderr)
    graph = load(ROOT / "pipelines" / case / "task_graph.json")
    for item in graph["artifacts"]:
        path = output / item["path"]
        assert path.is_file(), path
        if path.suffix == ".csv":
            assert set(item["required_columns"]) <= set(pd.read_csv(path, nrows=0).columns)
        elif path.suffix == ".json":
            load(path)


def check_credit(data, out):
    history = pd.read_csv(data / "credit_history.csv")
    integrated = pd.read_csv(out / "integrated.csv").set_index("application_id")
    expected = history.groupby("application_id").agg(count=("account_status", "size"), mean=("utilization_pct", "mean"), maximum=("balance", "max"), current=("account_status", lambda s: (s == "Current").sum()))
    np.testing.assert_allclose(integrated.loc[expected.index, "history_record_count"], expected["count"])
    np.testing.assert_allclose(integrated.loc[expected.index, "history_mean_utilization_pct"], expected["mean"])
    np.testing.assert_allclose(integrated.loc[expected.index, "history_max_balance"], expected["maximum"])
    np.testing.assert_allclose(integrated.loc[expected.index, "history_current_account_count"], expected["current"])
    train = pd.read_csv(out / "train.csv"); test = pd.read_csv(out / "test.csv"); predictions = pd.read_csv(out / "predictions.csv")
    assert len(train) == 375 and len(test) == len(predictions) == 125
    assert set(train.application_id).isdisjoint(test.application_id) and set(train.application_id) | set(test.application_id) == set(integrated.index)
    assert predictions.default_probability.between(0, 1).all()


def check_churn(data, out):
    transactions = pd.read_csv(data / "transactions.csv")
    metrics = pd.read_csv(out / "customer_metrics.csv").set_index("customer_id")
    transactions["is_discounted"] = (transactions.discount_applied > 0).astype(int)
    expected = transactions.groupby("customer_id").agg(count=("transaction_id", "size"), spend=("amount", "sum"), returns=("is_return", "sum"), discounted=("is_discounted", "sum"), discount=("discount_applied", "sum"))
    np.testing.assert_allclose(metrics.loc[expected.index, "transaction_count"], expected["count"])
    np.testing.assert_allclose(metrics.loc[expected.index, "total_spend"], expected["spend"])
    np.testing.assert_allclose(metrics.loc[expected.index, "return_count"], expected["returns"])
    np.testing.assert_allclose(metrics.loc[expected.index, "discounted_transaction_count"], expected["discounted"])
    np.testing.assert_allclose(metrics.loc[expected.index, "total_discount"], expected["discount"])
    report = load(out / "churn_report.json")
    assert report["customers"] == 500 and report["transactions"] == len(transactions) and report["cutoff_date"] == "2024-12-31"


def check_inventory(data, out):
    inventory = pd.read_csv(data / "inventory.csv")
    daily = pd.read_csv(out / "daily_demand.csv")
    plan = pd.read_csv(out / "inventory_plan.csv")
    assert len(daily) == len(inventory) * 90 and daily.groupby("sku_id").size().eq(90).all()
    assert np.allclose(plan.target_stock, plan.mean_daily_demand * plan.lead_time_days + 1.645 * plan.std_daily_demand * np.sqrt(plan.lead_time_days))
    positive = plan.suggested_order_quantity > 0
    assert (plan.loc[positive, "suggested_order_quantity"] % plan.loc[positive, "minimum_order_qty"] == 0).all()
    assert (plan.reorder_required == positive.astype(int)).all()


def check_recommendation(data, out):
    products = pd.read_csv(data / "products.csv").set_index("product_id")
    orders = pd.read_csv(data / "orders.csv")
    purchased = orders.groupby("customer_id").product_id.apply(set).to_dict()
    recs = pd.read_csv(out / "recommendations.csv")
    assert recs.groupby("customer_id").size().le(3).all()
    assert recs.groupby("customer_id")["rank"].apply(list).apply(lambda v: v == list(range(1, len(v) + 1))).all()
    assert all(products.loc[row.product_id, "in_stock"] == 1 and row.product_id not in purchased.get(row.customer_id, set()) for row in recs.itertuples())
    for _, group in recs.groupby("customer_id"):
        ordered = group.sort_values(["score", "product_id"], ascending=[False, True])
        assert ordered.product_id.tolist() == group.sort_values("rank").product_id.tolist()


def check_cluster(data, out):
    players = pd.read_csv(data / "data.csv")
    assigned = pd.read_csv(out / "player_clusters.csv")
    profiles = pd.read_csv(out / "cluster_profiles.csv")
    assert assigned.player_id.tolist() == sorted(players.player_id.tolist())
    assert set(assigned.cluster) == {0, 1, 2, 3} and profiles.player_count.sum() == len(players)
    means = assigned.groupby("cluster").efficiency_rating.mean()
    np.testing.assert_allclose(profiles.set_index("cluster").mean_efficiency_rating, means)
    report = load(out / "clustering_report.json")
    assert -1 <= report["silhouette_score"] <= 1 and sum(report["cluster_sizes"].values()) == len(players)


CHECKS = {"003_credit_risk": check_credit, "004_customer_churn": check_churn, "005_demand_forecasting": check_inventory, "006_ecommerce_recommendation": check_recommendation, "014_sports_clustering_integration_validation": check_cluster}


def corrupt(case, source, destination):
    shutil.copytree(source, destination)
    if case == "003_credit_risk":
        path = destination / "bureau_data.csv"; frame = pd.read_csv(path); frame.loc[0, "application_id"] = "UNKNOWN"; frame.to_csv(path, index=False)
    elif case == "004_customer_churn":
        path = destination / "transactions.csv"; frame = pd.read_csv(path); frame.loc[0, "customer_id"] = "UNKNOWN"; frame.to_csv(path, index=False)
    elif case == "005_demand_forecasting":
        path = destination / "sales_orders.csv"; frame = pd.read_csv(path); frame.loc[0, "sku_id"] = "UNKNOWN"; frame.to_csv(path, index=False)
    elif case == "006_ecommerce_recommendation":
        path = destination / "orders.csv"; frame = pd.read_csv(path); frame.loc[0, "product_id"] = "UNKNOWN"; frame.to_csv(path, index=False)
    else:
        path = destination / "data.csv"; frame = pd.read_csv(path); frame.loc[1, "player_id"] = frame.loc[0, "player_id"]; frame.to_csv(path, index=False)


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="inlumen-batch02-") as temp_name:
        temp = Path(temp_name)
        for case in CASES:
            source = ROOT / "pipelines" / case
            validate(load(source / "task_graph.json"), source)
            output = temp / (case + "-output")
            run(case, source / "inputs", output)
            CHECKS[case](source / "inputs", output)
            results.append({"case": case, "probe": "reference_outputs_and_independent_invariants", "status": "passed", "output_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}})
            invalid = temp / (case + "-invalid")
            corrupt(case, source / "inputs", invalid)
            run(case, invalid, temp / (case + "-invalid-output"), expect_failure=True)
            results.append({"case": case, "probe": "broken_identifier_contract_rejected", "status": "passed"})
            for track in ["natural_language", "fixed_graph"]:
                destination = export(case, temp / f"{case}-{track}", track)
                files = {str(path.relative_to(destination)) for path in destination.rglob("*") if path.is_file()}
                assert not any(Path(path).name in {"reference.py", "task_graph.json", "provenance.json", "requirements.txt"} for path in files)
                assert ("provided_graph.json" in files) == (track == "fixed_graph")
        results.append({"case": "batch-02", "probe": "generator_input_allowlist_both_tracks", "status": "passed"})
    report = {"status":"passed", "scope":"Batch-02 Python references, independent invariants, invalid-key rejection, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation", "dagster_runtime_qualification":"not_run", "review_status":"author_review_pending", "python":sys.version.split()[0], "packages":{name:version(name) for name in ["pandas","numpy","scikit-learn","jsonschema"]}, "checks":results}
    (ROOT / "qualification-report-batch02.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status":"passed", "check_groups":len(results), "dagster_runtime_qualification":"not_run"}, indent=2))


if __name__ == "__main__":
    main()
