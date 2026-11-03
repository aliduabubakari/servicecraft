"""Qualify every prepared control; preserve explicit failures and coverage gaps."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluation_models import EvaluationSpec
from app.evaluator import docker_run, evaluate
from app.control_compiler import asset_name


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark-root", type=Path, required=True)
    p.add_argument("--prepared", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cases", nargs="*")
    p.add_argument("--workers", type=int, default=2)
    args = p.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    benchmark = args.benchmark_root.resolve()
    prepared = args.prepared.resolve()
    oracle_image = json.loads(
        subprocess.check_output(["docker", "image", "inspect", "servicecraft-oracle:corpus-v1"])
    )[0]["Id"]
    runtime_image = json.loads(
        subprocess.check_output(["docker", "image", "inspect", "servicecraft-runtime:1.13.12"])
    )[0]["Id"]
    batches = {
        row["pipeline_id"]: int(path.stem.split("-")[-1])
        for path in benchmark.glob("batch-*.json")
        for row in json.loads(path.read_text())["cases"]
    }

    def qualify(case):
        work = root / case.name
        work.mkdir()
        try:
            graph = json.loads((case / "task_graph.json").read_text())
            expected = work / "private" / "expected"
            expected.mkdir(parents=True)
            expected.chmod(0o777)
            spec = EvaluationSpec.model_validate(
                {
                    "schema_version": "servicecraft.evaluation-spec@1",
                    "case_id": case.name,
                    "module": "definitions",
                    "image": runtime_image,
                    "expected_nodes": [asset_name(t["id"]) for t in graph["tasks"]],
                    "expected_edges": [
                        [asset_name(e["source"]), asset_name(e["target"])]
                        for e in graph["dependencies"]
                    ],
                    "artifacts": [
                        {
                            "path": a["path"],
                            "format": a["format"] if a["format"] in ["csv", "json"] else "file",
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
                        if a["format"] in ["csv", "json"]
                    ],
                    "timeout_seconds": 900,
                    "memory": "2g",
                    "required_packages": {
                        "dagster": "1.13.12",
                        "numpy": "2.0.1",
                        "pandas": "2.2.2",
                        "scikit-learn": "1.5.1",
                        "scipy": "1.14.1",
                        "openpyxl": "3.1.5",
                    },
                    "required_imports": [
                        "dagster",
                        "numpy",
                        "pandas",
                        "sklearn",
                        "scipy",
                        "openpyxl",
                    ],
                }
            )
            reference = docker_run(
                spec.image,
                [
                    (benchmark, "/benchmark", True),
                    (case / "inputs", "/inputs", True),
                    (expected, "/reference-output", False),
                ],
                [
                    "python",
                    f"/benchmark/pipelines/{case.name}/reference.py",
                    "--data-dir",
                    "/inputs",
                    "--output-dir",
                    "/reference-output",
                ],
                spec,
                work / "reference.log",
            )
            if reference["status"] != "pass":
                return {"case": case.name, "status": "reference_failed", "detail": reference}
            oracle = work / "private" / "oracle"
            oracle.mkdir()
            oracle_benchmark = oracle / "benchmark"
            (oracle_benchmark / "tools").mkdir(parents=True)
            for name in [
                f"qualify_batch{batches[case.name]:02d}.py",
                "validate_specs.py",
                "export_inputs.py",
                "prompt_format.py",
            ]:
                shutil.copyfile(benchmark / "tools" / name, oracle_benchmark / "tools" / name)
            shutil.copyfile(
                benchmark / "task-graph.schema.json", oracle_benchmark / "task-graph.schema.json"
            )
            oracle_case = oracle_benchmark / "pipelines" / case.name
            oracle_case.mkdir(parents=True)
            for name in ["task_graph.json", "provenance.json", "description.md"]:
                shutil.copyfile(benchmark / "pipelines" / case.name / name, oracle_case / name)
            shutil.copytree(case / "inputs", oracle_case / "inputs")
            shutil.copytree(expected, oracle / "expected")
            shutil.copyfile(
                Path(__file__).with_name("corpus_oracle_worker.py"), oracle / "check.py"
            )
            (oracle / "config.json").write_text(
                json.dumps(
                    {"case": case.name, "checker_module": f"qualify_batch{batches[case.name]:02d}"}
                )
            )
            spec = spec.model_copy(
                update={
                    "external_oracles": [
                        __import__(
                            "app.evaluation_models", fromlist=["ExternalOracle"]
                        ).ExternalOracle(
                            id="independent-assertions-and-model-probes",
                            directory="oracle",
                            image=oracle_image,
                        )
                    ]
                }
            )
            path = work / "private/evaluation.json"
            path.write_text(spec.model_dump_json(indent=2))
            result = evaluate(
                case / "candidate",
                case / "inputs",
                path,
                work / "report",
                {"method": "reference_derived_control", "not_llm_experiment": True},
            )
            return {
                "case": case.name,
                "status": "control_passed"
                if result["scores"]["complete_success"] == 1
                else "control_failed",
                "scores": result["scores"],
                "stages": {k: v["status"] for k, v in result["stages"].items()},
                "model_artifacts": [a["path"] for a in graph["artifacts"] if a["format"] == "pkl"],
                "oracle_checks": result["stages"]["oracle"].get("external", []),
                "paper_admission": "automated_checks_passed_author_review_pending"
                if result["scores"]["complete_success"] == 1
                else "not_admitted",
            }
        except Exception as exc:
            return {
                "case": case.name,
                "status": "preparation_failed",
                "error": str(exc),
                "paper_admission": "not_admitted",
            }

    cases = [
        x
        for x in sorted(prepared.iterdir())
        if x.is_dir() and (not args.cases or x.name in args.cases)
    ]
    records = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(qualify, c) for c in cases]):
            row = future.result()
            records.append(row)
            print(json.dumps(row), flush=True)
            (root / "qualification.json").write_text(
                json.dumps(sorted(records, key=lambda x: x["case"]), indent=2)
            )
    return int(any(r["status"] != "control_passed" for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
