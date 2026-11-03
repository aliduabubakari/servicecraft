"""Public corpus completeness checks; private fixtures are not required by these tests."""

import json
from pathlib import Path


def test_every_numbered_case_has_a_qualified_control_and_profile():
    root = Path(__file__).resolve().parents[1] / "corpus"
    registry = json.loads((root / "registry.json").read_text())
    assert registry["case_count"] == registry["qualified_cases"] == 100
    assert {int(r["case_id"].split("_")[0]) for r in registry["cases"]} == set(range(1, 101))
    for row in registry["cases"]:
        assert row["status"] == "runtime_and_oracle_qualified"
        assert row["dependency_profile"] in registry["profiles"]
        assert (root / row["control"] / "definitions.py").is_file()
        assert (root / row["evaluation_spec"]).is_file()
        assert row["negative_qualification"]["status"] == "pass"


def test_model_and_oracle_coverage_is_explicit():
    summary = json.loads(
        (Path(__file__).resolve().parents[1] / "corpus/qualification-summary.json").read_text()
    )
    assert summary["runtime_and_independent_oracle_passes"] == 100
    assert summary["required_input_column_rejections"] == 100
    assert summary["missing_output_rejections"] == 100
    assert summary["serialized_models_behaviorally_probed_and_corruptions_rejected"] == 47
    assert summary["artifacts_by_format"] == {"csv": 472, "json": 132, "file": 47}
    assert summary["author_semantic_review"] == {"author_review_pending": 100}
