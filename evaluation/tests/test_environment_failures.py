from app.evaluator import evaluate
from test_evaluator import specification


def test_missing_benchmark_inputs_are_infrastructure(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "definitions.py").write_text("x=1")
    (tmp_path / "answer.json").write_text('{"sum":6}')
    spec = tmp_path / "spec.json"
    spec.write_text(specification().model_dump_json())
    result = evaluate(candidate, tmp_path / "missing-inputs", spec, tmp_path / "report")
    assert result["stages"]["submission"]["status"] == "infra_error"
    assert all(v is None for v in result["scores"].values())


def test_missing_generated_submission_is_candidate_failure(tmp_path):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (tmp_path / "answer.json").write_text('{"sum":6}')
    spec = tmp_path / "spec.json"
    spec.write_text(specification().model_dump_json())
    result = evaluate(tmp_path / "missing-submission", inputs, spec, tmp_path / "report")
    assert result["stages"]["submission"]["status"] == "fail"
    assert result["scores"]["complete_success"] == 0
