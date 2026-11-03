"""Assemble only evidenced controls; retain explicit unadmitted cases in the registry."""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluator import hashes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--benchmark-root", type=Path, required=True)
    p.add_argument("--prepared", type=Path, nargs="+", required=True)
    p.add_argument("--qualifications", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    benchmark = args.benchmark_root.resolve()
    evidence = {}
    for folder in args.qualifications:
        for row in json.loads((folder / "qualification.json").read_text()):
            if (
                row["status"] == "control_passed"
                and all(x["status"] == "pass" for x in row.get("oracle_checks", []))
                and row.get("oracle_checks")
            ):
                evidence[row["case"]] = (row, folder.resolve() / row["case"])
    registry = []
    profiles = {}
    controls = {}
    entries = []
    for graph_path in sorted((benchmark / "pipelines").glob("*/task_graph.json")):
        graph = json.loads(graph_path.read_text())
        case = graph["pipeline_id"]
        row = {
            "case_id": case,
            "task_count": len(graph["tasks"]),
            "topology": graph["topology"],
            "author_review": graph.get("review_status", "unrecorded"),
            "source_graph_sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest(),
        }
        if case not in evidence:
            row.update(
                status="not_admitted", reason="No complete runtime and independent-oracle evidence"
            )
            registry.append(row)
            continue
        checked, folder = evidence[case]
        result = json.loads((folder / "report/result.json").read_text())
        source = next(
            (
                p.resolve() / case
                for p in args.prepared
                if hashes(p.resolve() / case / "candidate") == result["candidate_sha256"]
            ),
            None,
        )
        if source is None:
            raise ValueError(f"Qualified control sources changed for {case}")
        dest = root / "cases" / case
        dest.mkdir(parents=True)
        shutil.copytree(source / "candidate", dest / "candidate")
        shutil.copytree(source / "inputs", dest / "inputs")
        shutil.copytree(folder / "private", dest / "private")
        shutil.copytree(folder / "report", dest / "qualification")
        spec = json.loads((dest / "private/evaluation.json").read_text())
        spec["image"] = result["runtime_image"]["id"]
        for oracle in spec["oracles"]:
            oracle["reference"] = "private/" + oracle["reference"]
        for oracle in spec["external_oracles"]:
            oracle["directory"] = "private/" + oracle["directory"]
        (dest / "evaluation.json").write_text(json.dumps(spec, indent=2))
        profile_name = "scientific-v1"
        profile = {
            "image": result["runtime_image"]["id"],
            "required_packages": spec["required_packages"],
            "required_imports": spec["required_imports"],
        }
        if profile_name in profiles and profiles[profile_name] != profile:
            raise ValueError("Conflicting runtime profiles")
        profiles[profile_name] = profile
        sub = {
            "candidate": f"cases/{case}/candidate",
            "inputs": f"cases/{case}/inputs",
            "spec": f"cases/{case}/evaluation.json",
        }
        controls[case] = {**sub, "profile": profile_name}
        entries.append(
            {
                **sub,
                "id": "control_" + case[:3],
                "control": case,
                "metadata": {"method": "trusted_control_smoke", "not_llm_experiment": True},
            }
        )
        row.update(
            status="runtime_and_oracle_qualified",
            dependency_profile=profile_name,
            control=sub["candidate"],
            evaluation_spec=sub["spec"],
            qualification_evidence=f"cases/{case}/qualification/result.json",
            input_sha256=result["input_sha256"],
            candidate_sha256=result["candidate_sha256"],
            oracle_checks=checked["oracle_checks"],
            artifact_count=len(graph["artifacts"]),
            logical_to_asset={
                t["id"]: "context_features" if t["id"] == "context" else t["id"]
                for t in graph["tasks"]
            },
        )
        registry.append(row)
    report = {
        "schema_version": "servicecraft.corpus-registry@1",
        "case_count": len(registry),
        "qualified_cases": sum(r["status"] == "runtime_and_oracle_qualified" for r in registry),
        "profiles": profiles,
        "cases": registry,
        "review_scope": "Automated stage mapping, graph, artifact, independent invariant and model-probe qualification; source author signoff unchanged",
    }
    (root / "registry.json").write_text(json.dumps(report, indent=2))
    (root / "control-smoke-experiment.json").write_text(
        json.dumps(
            {
                "schema_version": "servicecraft.experiment@1",
                "profiles": profiles,
                "controls": controls,
                "entries": entries,
            },
            indent=2,
        )
    )
    print(json.dumps({"cases": len(registry), "qualified": report["qualified_cases"]}))
    return int(report["qualified_cases"] != len(registry))


if __name__ == "__main__":
    raise SystemExit(main())
