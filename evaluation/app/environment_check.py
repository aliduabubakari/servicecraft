"""Evaluator-owned environment preflight; never imports candidate code."""

import importlib
import json
from importlib.metadata import version
from pathlib import Path

protocol = json.loads(Path("/protocol/runtime.json").read_text())
checks = []
for name, expected in protocol["required_packages"].items():
    try:
        actual = version(name)
        checks.append(
            {"package": name, "expected": expected, "actual": actual, "passed": actual == expected}
        )
    except Exception as exc:
        checks.append({"package": name, "passed": False, "error": str(exc)})
for name in protocol["required_imports"]:
    try:
        importlib.import_module(name)
        checks.append({"import": name, "passed": True})
    except Exception as exc:
        checks.append({"import": name, "passed": False, "error": str(exc)})
Path("/evidence/environment.json").write_text(
    json.dumps(
        {"status": "pass" if all(c["passed"] for c in checks) else "infra_error", "checks": checks},
        indent=2,
    )
)
