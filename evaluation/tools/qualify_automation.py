"""Exercise the real batch CLI with two benchmark controls and deliberate failures."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    pilot = args.pilot_dir.resolve()
    profile = json.loads(
        (Path(__file__).resolve().parents[1] / "profiles/scientific.json").read_text()
    )
    controls = {}
    entries = []
    for name in [
        "100_transportation_visualization_v2",
        "053_sports_visualization_validation_recovery",
    ]:
        case = pilot / name
        sub = {
            "candidate": str(case / "candidate"),
            "inputs": str(case / "inputs"),
            "spec": str(case / "private/evaluation.json"),
        }
        controls[name] = {**sub, "profile": "scientific"}
        entries.append(
            {
                **sub,
                "id": "valid_" + name[:3],
                "control": name,
                "metadata": {"method": "authored_control", "track": "fixed_graph", "repetition": 0},
            }
        )
    sub = {k: entries[0][k] for k in ["candidate", "inputs", "spec"]}
    for fault in ["missing_import", "wrong_value"]:
        dest = root / fault
        shutil.copytree(sub["candidate"], dest)
        source = dest / "definitions.py"
        code = source.read_text()
        if fault == "missing_import":
            code = "import nonexistent_servicecraft_qualification_package\n" + code
        else:
            code = code.replace(
                "float(chart.iloc[0].total_passenger_km)",
                "float(chart.iloc[0].total_passenger_km) + 1000",
            )
        source.write_text(code)
        entries.append(
            {
                **sub,
                "candidate": str(dest),
                "id": fault,
                "control": entries[0]["control"],
                "metadata": {"method": "injected_failure"},
            }
        )
    controls["broken"] = {**controls[entries[0]["control"]], "profile": "broken"}
    entries.append({**sub, "id": "blocked_environment", "control": "broken"})
    manifest = {
        "schema_version": "servicecraft.experiment@1",
        "profiles": {
            "scientific": profile,
            "broken": {**profile, "required_packages": {"dagster": "0.0.0"}},
        },
        "controls": controls,
        "entries": entries,
        "infrastructure_retries": 1,
    }
    path = root / "experiment.json"
    path.write_text(json.dumps(manifest, indent=2))
    command = [
        sys.executable,
        "-m",
        "app.service_craft",
        "batch",
        str(path),
        "--output",
        str(root / "batch"),
    ]
    proc = subprocess.run(command, capture_output=True, text=True)
    if proc.returncode != 2:
        raise RuntimeError(
            f"Expected unavailable environment exit code 2: {proc.stdout} {proc.stderr}"
        )
    summary = json.loads(proc.stdout)
    rows = {r["id"]: r for r in summary["entries"]}
    assert (
        summary["scheduled"] == 5
        and summary["complete_successes"] == 2
        and summary["unavailable"] == 1
    )
    assert rows["missing_import"]["scores"]["dagster_executable"] == 0
    assert (
        rows["wrong_value"]["scores"]["dagster_executable"] == 1
        and rows["wrong_value"]["scores"]["behaviorally_correct"] == 0
    )
    before = {str(p): p.stat().st_mtime_ns for p in (root / "batch").rglob("result.json")}
    resumed = subprocess.run(command + ["--resume"], capture_output=True, text=True)
    assert resumed.returncode == 2, resumed.stderr
    assert before == {str(p): p.stat().st_mtime_ns for p in (root / "batch").rglob("result.json")}
    report = {
        "status": "pass",
        "scheduled": 5,
        "correct_controls": 2,
        "detected_candidate_failures": 2,
        "blocked_environment": 1,
        "resume_reexecuted_attempts": 0,
        "scope": "Evaluator automation controls, not paper generation results",
    }
    (root / "qualification.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
