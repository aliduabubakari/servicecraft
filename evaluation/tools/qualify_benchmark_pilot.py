"""Prepare two real-data smoke controls and qualify mounts, dependencies and scoring."""

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluation_models import EvaluationSpec
from app.evaluator import docker_run, evaluate

CASES = {
    "route_linear": "100_transportation_visualization_v2",
    "player_fanout": "053_sports_visualization_validation_recovery",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    benchmark, root = args.benchmark_root.resolve(), args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    outcomes = []
    for alias, case in CASES.items():
        source = benchmark / "pipelines" / case
        graph = json.loads((source / "task_graph.json").read_text())
        run = root / case
        inputs, candidate, private = (run / n for n in ["inputs", "candidate", "private"])
        shutil.copytree(source / "inputs", inputs)
        shutil.copytree(
            Path(__file__).resolve().parents[1] / "pilots" / alias,
            candidate,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        expected = private / "expected"
        expected.mkdir(parents=True, mode=0o777)
        expected.chmod(0o777)
        spec = EvaluationSpec.model_validate(
            {
                "schema_version": "servicecraft.evaluation-spec@1",
                "case_id": case,
                "module": "definitions",
                "expected_nodes": [t["id"] for t in graph["tasks"]],
                "expected_edges": [[e["source"], e["target"]] for e in graph["dependencies"]],
                "artifacts": [
                    {
                        "path": a["path"],
                        "format": a["format"],
                        "required_columns": a.get("required_columns", []),
                    }
                    for a in graph["artifacts"]
                ],
                "oracles": [
                    {
                        "id": a["id"],
                        "artifact": a["path"],
                        "kind": "csv_equals" if a["format"] == "csv" else "json_equals",
                        "reference": "expected/" + a["path"],
                    }
                    for a in graph["artifacts"]
                ],
                "required_packages": {"dagster": "1.13.12", "numpy": "2.0.1", "pandas": "2.2.2"},
                "required_imports": ["dagster", "numpy", "pandas"],
            }
        )
        control = docker_run(
            spec.image,
            [
                (benchmark, "/benchmark", True),
                (inputs, "/inputs", True),
                (expected, "/reference-output", False),
            ],
            [
                "python",
                f"/benchmark/pipelines/{case}/reference.py",
                "--data-dir",
                "/inputs",
                "--output-dir",
                "/reference-output",
            ],
            spec,
            run / "reference.log",
        )
        if control["status"] != "pass":
            raise RuntimeError(
                f"Reference environment control failed: {control}; see {run}/reference.log"
            )
        spec_path = private / "evaluation.json"
        spec_path.write_text(spec.model_dump_json(indent=2))
        result = evaluate(
            candidate,
            inputs,
            spec_path,
            run / "report",
            {"method": "authored_smoke_control", "not_llm_experiment": True},
        )
        outcome = {
            "case": case,
            "environment": result.get("environment"),
            "scores": result["scores"],
        }
        outcomes.append(outcome)
        print(json.dumps(outcome), flush=True)
    # An approved-profile package mismatch must never be a candidate zero.
    bad = spec.model_copy(update={"required_packages": {"dagster": "0.0.0"}})
    bad_path = private / "broken-environment.json"
    bad_path.write_text(bad.model_dump_json(indent=2))
    negative = evaluate(candidate, inputs, bad_path, root / "broken-environment-report")
    infra_correct = (
        negative["scores"]["complete_success"] is None
        and negative["environment"]["status"] == "infra_error"
    )
    summary = {
        "status": "pass"
        if all(o["scores"]["complete_success"] == 1 for o in outcomes) and infra_correct
        else "fail",
        "scope": "Visible-data smoke controls; no LLM generations or full benchmark certification",
        "cases": outcomes,
        "broken_environment_correctly_unscored": infra_correct,
    }
    (root / "summary.json").write_text(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
