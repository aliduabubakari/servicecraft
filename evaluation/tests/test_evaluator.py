import pytest
from pydantic import ValidationError

from app.evaluation_models import EvaluationResult, EvaluationSpec
from app.evaluator import (
    check_contracts,
    check_oracles,
    contained,
    equivalent,
    evaluate,
    graph_score,
)


def specification():
    return EvaluationSpec.model_validate(
        {
            "schema_version": "servicecraft.evaluation-spec@1",
            "case_id": "sum",
            "module": "definitions",
            "expected_nodes": ["read", "sum"],
            "expected_edges": [["read", "sum"]],
            "artifacts": [{"path": "answer.json", "format": "json", "required_keys": ["sum"]}],
            "oracles": [
                {
                    "id": "sum_correct",
                    "artifact": "answer.json",
                    "kind": "json_equals",
                    "reference": "answer.json",
                }
            ],
        }
    )


def test_valid_schema_wrong_values_fail(tmp_path):
    out, private = tmp_path / "out", tmp_path / "private"
    out.mkdir()
    private.mkdir()
    (out / "answer.json").write_text('{"sum": 999}')
    (private / "answer.json").write_text('{"sum": 6}')
    spec = specification()
    assert check_contracts(out, spec)["status"] == "pass"
    assert check_oracles(out, private, spec)["status"] == "fail"


def test_strict_oracle_semantics():
    assert equivalent({"x": 1.0000001}, {"x": 1}, 1e-6, 1e-6)
    assert not equivalent({"x": True}, {"x": 1}, 1e-6, 1e-6)
    assert not equivalent([1, 2], [2, 1], 1e-6, 1e-6)
    assert not equivalent(float("nan"), 1, 1e-6, 1e-6)


def test_missing_and_extra_dependencies_fail():
    spec = specification()
    result = graph_score({"nodes": ["read", "sum"], "edges": []}, spec)
    assert result["status"] == "fail"
    assert result["structure_score_01"] == pytest.approx(2 / 3)
    assert (
        graph_score({"nodes": ["read", "sum", "extra"], "edges": [["read", "sum"]]}, spec)["status"]
        == "fail"
    )


def test_path_and_symlink_escape(tmp_path):
    with pytest.raises(ValueError):
        contained(tmp_path, "../escape", exists=False)
    (tmp_path / "link").symlink_to("/etc/passwd")
    with pytest.raises(ValueError):
        contained(tmp_path, "link")


def test_missing_evidence_never_passes(tmp_path):
    source, inputs = tmp_path / "source", tmp_path / "inputs"
    source.mkdir()
    inputs.mkdir()
    spec = tmp_path / "spec.json"
    spec.write_text(specification().model_dump_json())
    (tmp_path / "answer.json").write_text('{"sum": 6}')
    result = evaluate(source, inputs, spec, tmp_path / "report")
    assert result["scores"]["complete_success"] == 0
    assert result["stages"]["submission"]["status"] == "fail"
    assert result["stages"]["oracle"]["status"] == "not_reached"
    EvaluationResult.model_validate(result)


def test_protocol_requires_oracles():
    data = specification().model_dump()
    data["oracles"] = []
    with pytest.raises(ValidationError):
        EvaluationSpec.model_validate(data)


def test_nonfinite_json_and_missing_artifact(tmp_path):
    (tmp_path / "answer.json").write_text('{"sum": NaN}')
    assert check_contracts(tmp_path, specification())["status"] == "fail"
    (tmp_path / "answer.json").unlink()
    assert check_contracts(tmp_path, specification())["status"] == "fail"


def test_bad_private_oracle_is_infrastructure(tmp_path):
    source, inputs = tmp_path / "source", tmp_path / "inputs"
    source.mkdir()
    inputs.mkdir()
    spec = tmp_path / "spec.json"
    spec.write_text(specification().model_dump_json())
    result = evaluate(source, inputs, spec, tmp_path / "report")
    assert result["scores"]["complete_success"] is None
    assert result["stages"]["submission"]["status"] == "infra_error"
    EvaluationResult.model_validate(result)


def test_success_requires_all_six_stages():
    data = {
        "schema_version": "servicecraft.evaluation-result@1",
        "run_id": "test",
        "metadata": {},
        "elapsed_seconds": 0,
        "stages": {
            s: {"status": "not_reached"}
            for s in (
                "submission",
                "static",
                "definition_graph",
                "execution",
                "contracts",
                "oracle",
            )
        },
        "scores": {
            s: 1
            for s in (
                "dagster_executable",
                "output_contract_valid",
                "behaviorally_correct",
                "complete_success",
            )
        },
    }
    with pytest.raises(ValidationError):
        EvaluationResult.model_validate(data)
