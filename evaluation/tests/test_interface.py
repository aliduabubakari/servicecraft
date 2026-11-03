import json

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.evaluation_models import EvaluationSpec
from app.main import app
from app.service_craft import main


def test_cli_eval_routes_arguments_and_metadata(monkeypatch, tmp_path, capsys):
    captured = {}

    def fake(candidate, inputs, spec, report_dir, metadata):
        captured.update(candidate=candidate, metadata=metadata)
        return {"scores": {"complete_success": 1}}

    monkeypatch.setattr("app.service_craft.evaluate", fake)
    assert (
        main(
            [
                "eval",
                str(tmp_path),
                "--inputs",
                str(tmp_path),
                "--spec",
                "spec.json",
                "--report-dir",
                "report",
                "--metadata",
                '{"method":"direct"}',
            ]
        )
        == 0
    )
    assert captured["candidate"] == tmp_path
    assert captured["metadata"] == {"method": "direct"}
    assert json.loads(capsys.readouterr().out)["scores"]["complete_success"] == 1


def test_api_is_independent_of_deployment_and_repair():
    client = TestClient(app)
    assert client.get("/health").json()["service"] == "servicecraft"
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/health", "/evaluate"}


def test_application_specific_spec_namespace_is_not_accepted():
    with pytest.raises(ValidationError):
        EvaluationSpec.model_validate({"schema_version": "inlumen.evaluation-spec@1"})
