"""Trusted, isolated independent assertions and serialized model probes."""

import importlib
import json
import pickle
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd


def probe_model(actual_path, expected_path, table_dir):
    actual = pickle.loads(actual_path.read_bytes())
    expected = pickle.loads(expected_path.read_bytes())
    if isinstance(expected, dict):
        features = expected["features"]
        e = expected["model"]
        scaler_e = expected.get("scaler")
    else:
        e = expected
        features = list(e.feature_names_in_)
        scaler_e = None
    a = actual["model"] if isinstance(actual, dict) else actual
    scaler_a = actual.get("scaler") if isinstance(actual, dict) else None
    for table in sorted(table_dir.glob("*.csv")):
        frame = pd.read_csv(table)
        if set(features) <= set(frame.columns):
            frame = frame[features].dropna()
            if not len(frame):
                continue
            frame = frame.iloc[np.linspace(0, len(frame) - 1, min(len(frame), 256), dtype=int)]
            xe = scaler_e.transform(frame) if scaler_e is not None else frame
            xa = scaler_a.transform(frame) if scaler_a is not None else frame
            method = "predict_proba" if hasattr(e, "predict_proba") else "predict"
            actual_values = getattr(a, method)(xa)
            expected_values = getattr(e, method)(xe)
            if method == "predict" and isinstance(expected, dict):
                expected_mapping = expected.get("mapping", expected.get("canonical_mapping"))
                actual_mapping = (
                    actual.get("mapping", actual.get("canonical_mapping"))
                    if isinstance(actual, dict)
                    else None
                )
                if expected_mapping is not None:
                    expected_values = np.array([expected_mapping[int(v)] for v in expected_values])
                    if actual_mapping is not None:
                        actual_values = np.array([actual_mapping[int(v)] for v in actual_values])
            np.testing.assert_allclose(actual_values, expected_values, atol=1e-6, rtol=1e-6)
            return {
                "model": actual_path.name,
                "status": "pass",
                "probe_table": table.name,
                "probe_rows": len(frame),
                "method": method,
            }
    raise ValueError(f"No qualified probe matrix for {expected_path.name}: {features}")


def main():
    config = json.loads(Path("/oracle/config.json").read_text())
    case = config["case"]
    sys.path.insert(0, "/oracle/benchmark/tools")
    mod = importlib.import_module(config["checker_module"])
    data = Path("/inputs")
    out = Path("/outputs")
    checks = []
    try:
        from validate_specs import validate

        case_dir = Path("/oracle/benchmark/pipelines") / case
        validate(json.loads((case_dir / "task_graph.json").read_text()), case_dir)
        checks.append({"id": "reference_graph_integrity", "status": "pass"})
        mapping = next(
            (getattr(mod, name) for name in ["CHECKERS", "CHECKS", "CHECK"] if hasattr(mod, name)),
            None,
        )
        if mapping is not None:
            mapping[case](data, out)
        else:
            getattr(mod, "inspect", getattr(mod, "check", None))(case, data, out)
        checks.append({"id": "independent_benchmark_assertions", "status": "pass"})
    except FileNotFoundError as exc:
        checks.append(
            {
                "id": "independent_benchmark_assertions",
                "status": "fail" if str(exc.filename).startswith("/outputs/") else "infra_error",
                "error": traceback.format_exc(),
            }
        )
    except Exception:
        checks.append(
            {
                "id": "independent_benchmark_assertions",
                "status": "fail",
                "error": traceback.format_exc(),
            }
        )
    expected = Path("/oracle/expected")
    for p in sorted(expected.glob("*.pkl")):
        try:
            checks.append(probe_model(out / p.name, p, expected))
        except Exception:
            checks.append({"model": p.name, "status": "fail", "error": traceback.format_exc()})
    report = {
        "status": "infra_error"
        if any(c["status"] == "infra_error" for c in checks)
        else "pass"
        if all(c["status"] == "pass" for c in checks)
        else "fail",
        "checks": checks,
    }
    Path("/evidence/oracle.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
