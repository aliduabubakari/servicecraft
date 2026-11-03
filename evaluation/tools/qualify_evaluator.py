"""Run real Docker qualification against five topologies and injected defects."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evaluator import evaluate

GRAPHS = {
    "linear": {"a": [], "b": ["a"], "c": ["b"]},
    "parallel": {"a": [], "b": []},
    "fan_out": {"a": [], "b": ["a"], "c": ["a"]},
    "fan_in": {"a": [], "b": [], "c": ["a", "b"]},
    "fan_in_fan_out": {"a": [], "b": [], "c": ["a", "b"], "d": ["c"], "e": ["c"]},
}


def fixture(root, name, graph, fault=None, mode="assets"):
    case = root / name
    candidate, inputs, private = (case / n for n in ("candidate", "inputs", "private"))
    for p in (candidate, inputs, private):
        p.mkdir(parents=True)
    (inputs / "data.json").write_text("[1,2,3]")
    header = "import json, os\nfrom pathlib import Path\nimport dagster as dg\n"
    body = []
    values = {}
    for node, parents in graph.items():
        values[node] = sum(values[p] for p in parents) if parents else 6
        expression = (
            " + ".join(parents)
            if parents
            else "sum(json.loads(Path('/inputs/data.json').read_text()))"
        )
        if fault == "wrong_value":
            expression = "999"
        code = f"@dg.asset\ndef {node}({', '.join(parents)}):\n"
        if fault == "runtime":
            code += '    raise RuntimeError("injected failure")\n'
        elif fault == "timeout":
            code += "    while True:\n        pass\n"
        else:
            code += f"    value = {expression}\n"
            if fault != "missing_output":
                code += f'    (Path(os.environ["SERVICECRAFT_OUTPUT_DIR"]) / "{node}.json").write_text(json.dumps({{"value": value}}))\n'
            code += "    return value\n"
        body.append(code)
        (private / f"{node}.json").write_text(json.dumps({"value": values[node]}))
    source = header + "\n".join(body) + f"\ndefs = dg.Definitions(assets=[{', '.join(graph)}])\n"
    if fault == "syntax":
        source += "\ndef broken(:\n"
    if fault == "import":
        source = "import nonexistent_qualification_package\n" + source
    if fault == "definition":
        source += '\n@dg.asset(required_resource_keys={"missing_resource"})\ndef needs_resource():\n    return 1\ndefs = dg.Definitions(assets=[a, b, c, needs_resource])\n'
    if mode == "job":
        source = source.replace("@dg.asset", "@dg.op")
        source = source[: source.index("\ndefs = ")]
        source += (
            "\n@dg.job\ndef pipeline():\n    c(b(a()))\n\ndefs = dg.Definitions(jobs=[pipeline])\n"
        )
    if mode == "callable":
        source = source.replace("defs = dg.Definitions", "def defs():\n    return dg.Definitions")
    if mode == "bundle":
        (candidate / "inputs").mkdir()
        (candidate / "outputs").mkdir()
        (candidate / "project").mkdir()
        source = source.replace("Path('/inputs/data.json')", "Path('../inputs/data.json')")
        source = source.replace('Path(os.environ["SERVICECRAFT_OUTPUT_DIR"])', "Path('../outputs')")
    if mode == "alias":
        source = source.replace("SERVICECRAFT_OUTPUT_DIR", "GENERATOR_OUTPUT_DIR")
    if fault == "failed_check":
        source += "\n@dg.asset_check(asset=a)\ndef required_check():\n    return dg.AssetCheckResult(passed=False)\ndefs = dg.Definitions(assets=[a, b, c], asset_checks=[required_check])\n"
    (candidate / ("project/definitions.py" if mode == "bundle" else "definitions.py")).write_text(
        source
    )
    spec = {
        "schema_version": "servicecraft.evaluation-spec@1",
        "case_id": name,
        "module": "definitions",
        "expected_nodes": list(graph),
        "expected_edges": [[p, n] for n, parents in graph.items() for p in parents],
        "artifacts": [
            {"path": f"{n}.json", "format": "json", "required_keys": ["value"]} for n in graph
        ],
        "oracles": [
            {
                "id": n,
                "artifact": f"{n}.json",
                "kind": "json_equals",
                "reference": f"{n}.json",
            }
            for n in graph
        ],
        # Static/container startup must finish before the intentional runtime hang.
        "timeout_seconds": 60 if fault == "timeout" else 120,
    }
    if mode == "job":
        spec.update(mode="job", job_name="pipeline")
    if mode == "alias":
        spec["environment_aliases"] = {"GENERATOR_OUTPUT_DIR": "output_dir"}
    if mode == "bundle":
        spec.update(
            project_dir="project",
            python_paths=["project"],
            bundle_inputs="inputs",
            bundle_outputs="outputs",
        )
    if fault == "wrong_graph":
        spec["expected_edges"] = []
    spec_path = private / "evaluation.json"
    spec_path.write_text(json.dumps(spec, indent=2))
    return candidate, inputs, spec_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Fresh directory for fixtures and all evidence")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    outcomes = []
    cases = [(n, g, None, "assets") for n, g in GRAPHS.items()]
    cases += [
        (f"fault_{f}", GRAPHS["linear"], f, "assets")
        for f in (
            "syntax",
            "import",
            "definition",
            "runtime",
            "timeout",
            "wrong_value",
            "missing_output",
            "wrong_graph",
            "failed_check",
        )
    ]
    cases += [
        ("native_job", GRAPHS["linear"], None, "job"),
        ("callable_definitions", GRAPHS["fan_in"], None, "callable"),
        ("bundle_relative_paths", GRAPHS["linear"], None, "bundle"),
        ("explicit_environment_alias", GRAPHS["fan_out"], None, "alias"),
    ]
    for name, graph, fault, mode in cases:
        candidate, inputs, spec = fixture(root, name, graph, fault, mode)
        result = evaluate(candidate, inputs, spec, root / name / "report")
        expected = int(fault is None)
        correct = result["scores"]["complete_success"] == expected
        static = result["stages"]["static"]
        correct &= static.get("measurement_version") == "servicecraft.raw-static@1"
        correct &= "diagnostic_mean_01" not in static and "scores" not in static
        if fault == "wrong_value":
            correct &= (
                result["scores"]["dagster_executable"] == 1
                and result["scores"]["output_contract_valid"] == 1
                and result["scores"]["behaviorally_correct"] == 0
            )
        if fault == "timeout":
            correct &= result["stages"]["execution"]["status"] == "timeout"
        expected_stages = {
            "syntax": "static",
            "import": "definition_graph",
            "definition": "definition_graph",
            "runtime": "execution",
            "missing_output": "contracts",
            "wrong_graph": "definition_graph",
            "failed_check": "execution",
            "wrong_value": "oracle",
        }
        if fault in expected_stages:
            correct &= result["stages"][expected_stages[fault]]["status"] == "fail"
        outcome = {
            "case": name,
            "expected_success": expected,
            "scores": result["scores"],
            "qualified": bool(correct),
        }
        outcomes.append(outcome)
        print(json.dumps(outcome), flush=True)
    report = {
        "status": "pass" if all(o["qualified"] for o in outcomes) else "fail",
        "cases": outcomes,
    }
    (root / "qualification.json").write_text(json.dumps(report, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
