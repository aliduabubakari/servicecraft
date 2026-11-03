import json

import pytest

from app.batch import run_batch


def setup(tmp_path, monkeypatch, verdicts):
    source = tmp_path / "source"
    source.mkdir()
    (source / "defs.py").write_text("x=1")
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "data").write_text("data")
    (tmp_path / "expected.json").write_text("{}")
    spec = {
        "schema_version": "servicecraft.evaluation-spec@1",
        "case_id": "case",
        "module": "defs",
        "expected_nodes": ["a"],
        "artifacts": [{"path": "answer.json", "format": "json"}],
        "oracles": [
            {
                "id": "a",
                "artifact": "answer.json",
                "kind": "json_equals",
                "reference": "expected.json",
            }
        ],
    }
    (tmp_path / "spec.json").write_text(json.dumps(spec))
    sub = {"candidate": "source", "inputs": "inputs", "spec": "spec.json"}
    manifest = {
        "schema_version": "servicecraft.experiment@1",
        "profiles": {
            "p": {
                "image": "test",
                "required_packages": {"dagster": "1.13.12"},
                "required_imports": ["dagster"],
            }
        },
        "controls": {"gold": {**sub, "profile": "p"}},
        "entries": [{**sub, "id": "run", "control": "gold"}],
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        "app.batch.subprocess.check_output", lambda *a, **k: b'[{"Id":"sha256:pinned"}]'
    )
    calls = []

    def fake(candidate, inputs, spec, report, metadata, **kw):
        calls.append(kw["runtime_profile"])
        score = verdicts.pop(0)
        result = {
            "schema_version": "servicecraft.evaluation-result@1",
            "run_id": "test",
            "metadata": metadata,
            "elapsed_seconds": 0,
            "scores": {
                k: score
                for k in [
                    "dagster_executable",
                    "output_contract_valid",
                    "behaviorally_correct",
                    "complete_success",
                ]
            },
            "stages": {
                k: {"status": "pass" if score == 1 else "infra_error" if score is None else "fail"}
                for k in [
                    "submission",
                    "static",
                    "definition_graph",
                    "execution",
                    "contracts",
                    "oracle",
                ]
            },
        }
        report.mkdir(parents=True)
        (report / "result.json").write_text(json.dumps(result))
        return result

    monkeypatch.setattr("app.batch.evaluate", fake)
    return path, calls


def test_resume_freezes_image_and_avoids_reruns(tmp_path, monkeypatch):
    manifest, calls = setup(tmp_path, monkeypatch, [1, 1])
    out = tmp_path / "reports"
    assert run_batch(manifest, out)["complete_successes"] == 1
    assert all(p["image"] == "sha256:pinned" for p in calls)
    assert run_batch(manifest, out, resume=True)["complete_successes"] == 1
    assert len(calls) == 2
    (tmp_path / "inputs" / "data").write_text("changed")
    with pytest.raises(ValueError, match="Resume rejected"):
        run_batch(manifest, out, resume=True)


def test_failed_control_blocks_candidate_without_zero(tmp_path, monkeypatch):
    manifest, calls = setup(tmp_path, monkeypatch, [0])
    result = run_batch(manifest, tmp_path / "reports")
    assert len(calls) == 1
    assert result["entries"][0]["status"] == "blocked_control"
    assert result["entries"][0]["scores"]["complete_success"] is None


def test_infrastructure_retry_preserves_each_attempt(tmp_path, monkeypatch):
    manifest, calls = setup(tmp_path, monkeypatch, [1, None, 1])
    data = json.loads(manifest.read_text())
    data["infrastructure_retries"] = 1
    manifest.write_text(json.dumps(data))
    out = tmp_path / "reports"
    assert run_batch(manifest, out)["complete_successes"] == 1
    assert (out / "entries/run/try-00/result.json").exists()
    assert (out / "entries/run/try-01/result.json").exists()


def test_candidate_failure_is_not_retried(tmp_path, monkeypatch):
    manifest, calls = setup(tmp_path, monkeypatch, [1, 0])
    data = json.loads(manifest.read_text())
    data["infrastructure_retries"] = 2
    manifest.write_text(json.dumps(data))
    assert run_batch(manifest, tmp_path / "reports")["complete_successes"] == 0
    assert len(calls) == 2


def test_all_entries_exported_even_when_blocked(tmp_path, monkeypatch):
    manifest, _ = setup(tmp_path, monkeypatch, [None])
    out = tmp_path / "reports"
    result = run_batch(manifest, out)
    assert result["scheduled"] == 1 and result["unavailable"] == 1
    assert len((out / "results.jsonl").read_text().splitlines()) == 1
    assert "blocked_control" in (out / "results.csv").read_text()


def test_interrupted_attempt_is_preserved_on_resume(tmp_path, monkeypatch):
    manifest, calls = setup(tmp_path, monkeypatch, [1, 1, 1])
    out = tmp_path / "reports"
    run_batch(manifest, out)
    attempt = out / "entries/run/try-00"
    (attempt / "result.json").unlink()
    (attempt / "partial.log").write_text("interrupted evidence")
    assert run_batch(manifest, out, resume=True)["complete_successes"] == 1
    assert (
        out / "entries/run/try-00-interrupted-0/partial.log"
    ).read_text() == "interrupted evidence"
    assert (attempt / "result.json").is_file()
    assert len(calls) == 3


def test_resume_freezes_private_oracle_code(tmp_path, monkeypatch):
    manifest, _ = setup(tmp_path, monkeypatch, [1, 1])
    context = tmp_path / "private-oracle"
    context.mkdir()
    (context / "check.py").write_text("pass")
    spec_path = tmp_path / "spec.json"
    spec = json.loads(spec_path.read_text())
    spec["external_oracles"] = [{"id": "private", "directory": "private-oracle", "image": "oracle"}]
    spec_path.write_text(json.dumps(spec))
    output = tmp_path / "reports"
    run_batch(manifest, output)
    (context / "check.py").write_text('raise RuntimeError("changed")')
    with pytest.raises(ValueError, match="Resume rejected"):
        run_batch(manifest, output, resume=True)
