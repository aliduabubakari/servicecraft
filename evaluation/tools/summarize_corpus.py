"""Verify assembled hashes and persist a compact corpus qualification report."""

import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluation_models import EvaluationSpec, EvaluationResult
from app.evaluator import hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    args = parser.parse_args()
    root = args.corpus.resolve()
    registry = json.loads((root / "registry.json").read_text())
    formats = Counter()
    groups = defaultdict(list)
    oracle_sources = set()
    for row in registry["cases"]:
        candidate = root / row["control"]
        spec = EvaluationSpec.model_validate_json((root / row["evaluation_spec"]).read_text())
        result = EvaluationResult.model_validate_json(
            (root / row["qualification_evidence"]).read_text()
        )
        assert hashes(candidate) == row["candidate_sha256"], row["case_id"]
        assert hashes(candidate.parent / "inputs") == row["input_sha256"], row["case_id"]
        assert (
            result.scores.complete_success == 1
            and row["negative_qualification"]["status"] == "pass"
        ), row["case_id"]
        context = candidate.parent / spec.external_oracles[0].directory
        assert hashes(context) == row["negative_qualification"]["oracle_context_sha256"], row[
            "case_id"
        ]
        oracle_sources.add(
            hashlib.sha256(
                ast.dump(
                    ast.parse((context / spec.external_oracles[0].script).read_text())
                ).encode()
            ).hexdigest()
        )
        formats.update(a.format for a in spec.artifacts)
        if (candidate / "plan.json").exists():
            sources = [
                s["source"] for s in json.loads((candidate / "plan.json").read_text())["steps"]
            ]
            digest = hashlib.sha256(
                (json.dumps(sources) + (candidate / "support.py").read_text()).encode()
            ).hexdigest()
        else:
            digest = hashlib.sha256((candidate / "native_reference.py").read_bytes()).hexdigest()
        row["reference_implementation_group"] = "implementation_" + digest[:16]
        groups[row["reference_implementation_group"]].append(row["case_id"])
    assert len(oracle_sources) == 1, "Private oracle implementations differ semantically"
    probes = [r["negative_qualification"] for r in registry["cases"]]
    summary = {
        "schema_version": "servicecraft.corpus-qualification@1",
        "cases": len(registry["cases"]),
        "runtime_and_independent_oracle_passes": sum(
            r["status"] == "runtime_and_oracle_qualified" for r in registry["cases"]
        ),
        "required_input_column_rejections": sum(p["invalid_input_rejected"] for p in probes),
        "missing_output_rejections": sum(p["missing_output_rejected"] for p in probes),
        "serialized_models_behaviorally_probed_and_corruptions_rejected": sum(
            p["models_probed"] for p in probes if p["corrupted_models_rejected"]
        ),
        "artifacts_by_format": dict(formats),
        "dependency_profiles": registry["profiles"],
        "topologies": dict(Counter(r["topology"] for r in registry["cases"])),
        "distinct_reference_code_fingerprints": len(groups),
        "reference_implementation_groups": dict(groups),
        "oracle_implementation_ast_sha256": next(iter(oracle_sources)),
        "author_semantic_review": dict(Counter(r["author_review"] for r in registry["cases"])),
        "scope": "Automated qualification on visible fixtures; not LLM generation results or author semantic signoff",
    }
    registry["implementation_groups"] = dict(groups)
    (root / "registry.json").write_text(json.dumps(registry, indent=2))
    (root / "qualification-summary.json").write_text(json.dumps(summary, indent=2))
    print(
        json.dumps(
            {
                k: v
                for k, v in summary.items()
                if k not in ["reference_implementation_groups", "dependency_profiles"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
