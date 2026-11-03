"""Negative qualification: required input columns and serialized-model corruption."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluation_models import EvaluationSpec
from app.evaluator import docker_run, check_oracles, hashes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--benchmark-root", required=True, type=Path)
    p.add_argument("--workers", default=3, type=int)
    args = p.parse_args()
    corpus = args.corpus.resolve()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    registry = json.loads((corpus / "registry.json").read_text())

    def probe(row):
        case = row["case_id"]
        source = corpus / "cases" / case
        work = root / case
        work.mkdir()
        try:
            spec = EvaluationSpec.model_validate_json((source / "evaluation.json").read_text())
            oracle = spec.external_oracles[0]
            oracle_context = source / oracle.directory
            shutil.copyfile(
                Path(__file__).with_name("corpus_oracle_worker.py"), oracle_context / oracle.script
            )
            shutil.copyfile(
                args.benchmark_root.resolve() / "pipelines" / case / "description.md",
                oracle_context / "benchmark/pipelines" / case / "description.md",
            )
            checked = (corpus / row["qualification_evidence"]).parent / "artifacts"

            def oracle_run(output_dir, name):
                oracle_evidence = work / name
                oracle_evidence.mkdir()
                oracle_evidence.chmod(0o777)
                result = docker_run(
                    oracle.image,
                    [
                        (oracle_context, "/oracle", True),
                        (source / "inputs", "/inputs", True),
                        (output_dir, "/outputs", True),
                        (oracle_evidence, "/evidence", False),
                    ],
                    ["python", f"/oracle/{oracle.script}"],
                    spec,
                    work / f"{name}.log",
                )
                detail = (
                    json.loads((oracle_evidence / "oracle.json").read_text())
                    if (oracle_evidence / "oracle.json").exists()
                    else {"status": "infra_error"}
                )
                detail["container"] = result
                return detail

            positive = oracle_run(checked, "positive-oracle")
            graph = json.loads((source / "candidate/graph.json").read_text())
            bad = work / "bad-inputs"
            shutil.copytree(source / "inputs", bad)
            input_item = graph["inputs"][0]
            filename = Path(input_item["path"]).name
            column = input_item["required_columns"][0]
            with (bad / filename).open(newline="") as h:
                reader = csv.DictReader(h)
                cols = [c for c in reader.fieldnames if c != column]
                records = list(reader)
            with (bad / filename).open("w", newline="") as h:
                writer = csv.DictWriter(h, fieldnames=cols, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(records)
            protocol = work / "protocol"
            protocol.mkdir()
            (protocol / "runtime.json").write_text(spec.model_dump_json())
            outputs = work / "outputs"
            evidence = work / "evidence"
            for folder in [outputs, evidence]:
                folder.mkdir()
                folder.chmod(0o777)
            result = docker_run(
                spec.image,
                [
                    (source / "candidate", "/candidate", True),
                    (bad, "/inputs", True),
                    (protocol, "/protocol", True),
                    (outputs, "/outputs", False),
                    (evidence, "/evidence", False),
                ],
                ["python", "/opt/evaluator/runtime_worker.py"],
                spec,
                work / "invalid-input.log",
            )
            runtime = (
                json.loads((evidence / "runtime.json").read_text())
                if (evidence / "runtime.json").exists()
                else {}
            )
            rejected = (
                result["status"] == "pass"
                and runtime.get("definition", {}).get("status") == "pass"
                and runtime.get("execution", {}).get("status") == "fail"
            )
            models = [a for a in spec.artifacts if a.path.endswith(".pkl")]
            model_probe = None
            if True:
                corrupted = work / "corrupted-model-outputs"
                shutil.copytree(checked, corrupted)
                for artifact in models:
                    (corrupted / artifact.path).write_bytes(
                        b"deliberately invalid serialized model"
                    )
                missing = next(a.path for a in spec.artifacts if a.format in {"csv", "json"})
                (corrupted / missing).unlink()
                oracle = spec.external_oracles[0]
                oracle_context = source / oracle.directory
                oracle_evidence = work / "model-evidence"
                oracle_evidence.mkdir()
                oracle_evidence.chmod(0o777)
                run = docker_run(
                    oracle.image,
                    [
                        (oracle_context, "/oracle", True),
                        (source / "inputs", "/inputs", True),
                        (corrupted, "/outputs", True),
                        (oracle_evidence, "/evidence", False),
                    ],
                    ["python", f"/oracle/{oracle.script}"],
                    spec,
                    work / "model-corruption.log",
                )
                report = (
                    json.loads((oracle_evidence / "oracle.json").read_text())
                    if (oracle_evidence / "oracle.json").exists()
                    else {}
                )
                failures = {
                    c["model"]
                    for c in report.get("checks", [])
                    if c.get("model") and c["status"] == "fail"
                }
                model_probe = run["status"] == "pass" and all(a.path in failures for a in models)
                omission_rejected = (
                    check_oracles(corrupted, source, spec)["status"] == "fail"
                    and report.get("status") != "infra_error"
                )
            return {
                "case_id": case,
                "missing_required_column": column,
                "invalid_input_rejected": rejected,
                "corrupted_models_rejected": model_probe,
                "models_probed": len(models),
                "positive_oracle": positive,
                "missing_output_rejected": omission_rejected,
                "oracle_context_sha256": hashes(oracle_context),
                "status": "pass"
                if rejected
                and model_probe is not False
                and omission_rejected
                and positive["status"] == "pass"
                else "fail",
            }
        except Exception as exc:
            return {"case_id": case, "status": "fail", "error": str(exc)}

    records = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed(
            [
                pool.submit(probe, r)
                for r in registry["cases"]
                if r["status"] == "runtime_and_oracle_qualified"
            ]
        ):
            row = future.result()
            records.append(row)
            print(json.dumps(row), flush=True)
            (root / "qualification.json").write_text(
                json.dumps(sorted(records, key=lambda r: r["case_id"]), indent=2)
            )
    indexed = {r["case_id"]: r for r in records}
    for row in registry["cases"]:
        result = indexed.get(row["case_id"], {"status": "fail", "error": "Missing probe result"})
        row["negative_qualification"] = result
        if result["status"] == "pass":
            row["oracle_checks"] = [result["positive_oracle"]]
        else:
            row["status"] = "not_admitted"
    registry["qualified_cases"] = sum(
        r["status"] == "runtime_and_oracle_qualified" for r in registry["cases"]
    )
    tmp = corpus / "registry.json.tmp"
    tmp.write_text(json.dumps(registry, indent=2))
    tmp.replace(corpus / "registry.json")
    return int(
        len(records) != registry["case_count"] or any(r["status"] != "pass" for r in records)
    )


if __name__ == "__main__":
    raise SystemExit(main())
