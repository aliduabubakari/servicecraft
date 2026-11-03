"""Raw tool measurements and direct scaling, with no custom weights or composite."""

import ast
import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path


def line_fraction(locations: set[tuple[str, int]], physical_lines: dict[str, int]) -> float:
    """Each physical source line contributes at most once, regardless of finding count."""
    valid = {
        (path, row)
        for path, row in locations
        if path in physical_lines and 1 <= row <= physical_lines[path]
    }
    return len(valid) / max(sum(physical_lines.values()), 1)


def analyze(root: Path) -> dict:
    root = root.resolve()
    files = sorted(root.rglob("*.py"))
    source = {str(p): p.read_text(encoding="utf-8") for p in files}
    physical_lines = {p: len(text.splitlines()) for p, text in source.items()}
    syntax_errors = []
    for path, text in source.items():
        try:
            ast.parse(text, filename=str(Path(path).relative_to(root)))
        except SyntaxError as exc:
            syntax_errors.append(
                {"file": str(Path(path).relative_to(root)), "line": exc.lineno, "message": exc.msg}
            )
    result = {
        "status": "pass" if not syntax_errors else "fail",
        "syntax_valid": not syntax_errors,
        "files": len(files),
        "physical_lines": sum(physical_lines.values()),
        "syntax_errors": syntax_errors,
        "measurement_version": "servicecraft.raw-static@1",
        "tools": {},
        "scaled_metrics": {},
    }
    commands = {
        "flake8": [str(root), "--isolated", "--format=%(path)s\t%(row)d\t%(col)d\t%(code)s"],
        "pylint": [str(p) for p in files]
        + ["--output-format=json", "--rcfile=/dev/null", "--persistent=no"],
        "bandit": ["-r", str(root), "-f", "json", "--ignore-nosec"],
    }
    for tool, args in commands.items():
        metric = f"{tool}_finding_line_fraction"
        try:
            tool_version = version(tool)
            proc = subprocess.run(
                [sys.executable, "-m", tool, *args], capture_output=True, text=True, timeout=60
            )
            if tool == "flake8":
                if proc.returncode not in (0, 1):
                    raise RuntimeError(proc.stderr)
                findings = [line.split("\t") for line in proc.stdout.splitlines() if line.strip()]
                locations = {(str(Path(f[0]).resolve()), int(f[1])) for f in findings}
                raw = {
                    "findings": len(findings),
                    "findings_per_100_lines": len(findings)
                    * 100
                    / max(result["physical_lines"], 1),
                }
            else:
                payload = json.loads(proc.stdout)
                if tool == "pylint":
                    if proc.returncode & 32 or not isinstance(payload, list):
                        raise RuntimeError(proc.stderr)
                    findings = payload
                    locations = {(str(Path(f["path"]).resolve()), f["line"]) for f in findings}
                    raw = {
                        "findings": len(findings),
                        "counts_by_type": {
                            k: sum(f["type"] == k for f in findings)
                            for k in ["fatal", "error", "warning", "refactor", "convention"]
                        },
                    }
                else:
                    if proc.returncode not in (0, 1) or payload.get("errors"):
                        raise RuntimeError(str(payload.get("errors") or proc.stderr))
                    findings = payload["results"]
                    locations = {
                        (str(Path(f["filename"]).resolve()), row)
                        for f in findings
                        for row in (f.get("line_range") or [f["line_number"]])
                    }
                    raw = {
                        "findings": len(findings),
                        "counts_by_severity": {
                            k: sum(f["issue_severity"] == k for f in findings)
                            for k in ["HIGH", "MEDIUM", "LOW"]
                        },
                    }
            fraction = line_fraction(locations, physical_lines)
            raw["distinct_flagged_physical_lines"] = round(fraction * result["physical_lines"])
            result["tools"][tool] = {"status": "pass", "version": tool_version, "raw": raw}
            result["scaled_metrics"][metric] = {
                "value": fraction,
                "direction": "lower_is_better",
                "formula": "distinct_physical_lines_with_findings / physical_source_lines",
            }
        except Exception as exc:
            result["tools"][tool] = {"status": "infra_error", "error": str(exc)}
            result["scaled_metrics"][metric] = {"value": None, "direction": "lower_is_better"}
    try:
        from radon.complexity import cc_visit
        from radon.metrics import mi_visit

        blocks, mi_by_file = [], {}
        for path, text in source.items():
            blocks.extend(b.complexity for b in cc_visit(text))
            mi_by_file[str(Path(path).relative_to(root))] = mi_visit(text, multi=True)
        mean_mi = sum(mi_by_file.values()) / len(mi_by_file) if mi_by_file else None
        result["tools"]["radon"] = {
            "status": "pass",
            "version": version("radon"),
            "raw": {
                "block_count": len(blocks),
                "mean_cc": sum(blocks) / len(blocks) if blocks else None,
                "max_cc": max(blocks, default=None),
                "maintainability_index_by_file": mi_by_file,
                "mean_file_maintainability_index": mean_mi,
            },
        }
        result["scaled_metrics"]["radon_maintainability_index_01"] = {
            "value": mean_mi / 100 if mean_mi is not None else None,
            "per_file": {p: mi / 100 for p, mi in mi_by_file.items()},
            "direction": "higher_is_better",
            "formula": "arithmetic_mean_of_native_file_MI / 100",
        }
    except Exception as exc:
        result["tools"]["radon"] = {"status": "infra_error", "error": str(exc)}
        result["scaled_metrics"]["radon_maintainability_index_01"] = {
            "value": None,
            "direction": "higher_is_better",
        }
    return result
