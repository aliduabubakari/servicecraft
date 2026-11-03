import importlib.util

import pytest

from app.static_analysis import analyze, line_fraction


def test_finding_line_fraction_has_no_severity_weights_or_duplicate_penalties():
    lines = {"a.py": 4, "b.py": 6}
    locations = {("a.py", 1), ("a.py", 1), ("b.py", 3), ("b.py", 0), ("other.py", 1)}
    assert line_fraction(locations, lines) == 2 / 10
    assert line_fraction(set(), {}) == 0


@pytest.mark.skipif(
    any(importlib.util.find_spec(name) is None for name in ("radon", "flake8", "pylint", "bandit")),
    reason="Install .[analysis] to exercise real static tools",
)
def test_real_tools_report_raw_values_and_direct_scaling(tmp_path):
    (tmp_path / "sample.py").write_text(
        '"""Example."""\nimport os\n\ndef unsafe(value):\n    return eval(value)\n'
    )
    result = analyze(tmp_path)
    assert result["measurement_version"] == "servicecraft.raw-static@1"
    assert "scores" not in result
    assert "diagnostic_mean_01" not in result
    assert all(t["status"] == "pass" for t in result["tools"].values())
    for tool in ("flake8", "pylint", "bandit"):
        raw = result["tools"][tool]["raw"]
        assert raw["findings"] > 0
        assert (
            result["scaled_metrics"][f"{tool}_finding_line_fraction"]["value"]
            == raw["distinct_flagged_physical_lines"] / result["physical_lines"]
        )
    raw_mi = result["tools"]["radon"]["raw"]["mean_file_maintainability_index"]
    assert result["scaled_metrics"]["radon_maintainability_index_01"]["value"] == raw_mi / 100
    assert result["tools"]["radon"]["raw"]["max_cc"] == 1


def test_missing_tools_are_unavailable(monkeypatch, tmp_path):
    (tmp_path / "sample.py").write_text('"""Example."""\n')

    def missing_version(_):
        raise RuntimeError("tool unavailable")

    monkeypatch.setattr("app.static_analysis.version", missing_version)
    result = analyze(tmp_path)
    assert result["tools"]["flake8"]["status"] == "infra_error"
    assert result["scaled_metrics"]["flake8_finding_line_fraction"]["value"] is None
