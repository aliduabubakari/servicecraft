"""Executed only inside the disposable runtime container; no private oracle access."""

import importlib
import json
import os
import sys
import traceback
from pathlib import Path


def main():
    import dagster as dg

    # Pinned Dagster 1.13.12 adapter; this helper is not exported at top level.
    from dagster._core.execution.api import create_execution_plan

    spec = json.loads(Path("/protocol/runtime.json").read_text())
    paths = {
        "input_dir": "/inputs",
        "input_manifest": "/inputs/input_manifest.json",
        "output_dir": "/outputs",
    }
    os.environ.update(
        {
            "SERVICECRAFT_INPUT_DIR": paths["input_dir"],
            "SERVICECRAFT_INPUT_MANIFEST": paths["input_manifest"],
            "SERVICECRAFT_OUTPUT_DIR": paths["output_dir"],
        }
    )
    os.environ.update(
        {alias: paths[target] for alias, target in spec["environment_aliases"].items()}
    )
    Path(os.environ["DAGSTER_HOME"]).mkdir(parents=True, exist_ok=True)
    os.chdir(Path("/candidate") / spec["project_dir"])
    sys.path[:0] = [str(Path("/candidate") / p) for p in spec["python_paths"]]
    report = {
        "dagster_version": dg.__version__,
        "python_version": sys.version,
        "packages": Path("/opt/evaluator/packages.txt").read_text().splitlines(),
        "definition": {"status": "not_reached"},
        "execution": {"status": "not_reached"},
    }
    try:
        obj = getattr(importlib.import_module(spec["module"]), spec["attribute"])
        definitions = (
            obj()
            if callable(obj) and not isinstance(obj, (dg.Definitions, dg.JobDefinition))
            else obj
        )
        if isinstance(definitions, dg.JobDefinition):
            definitions = dg.Definitions(jobs=[definitions])
        dg.Definitions.validate_loadable(definitions)
        if spec["mode"] == "assets":
            graph = definitions.resolve_asset_graph()
            keys = graph.get_all_asset_keys()
            nodes = sorted(k.to_user_string() for k in keys)
            edges = sorted(
                [p.to_user_string(), k.to_user_string()]
                for k in keys
                for p in graph.get(k).parent_keys
            )
            job = definitions.resolve_implicit_global_asset_job_def()
        else:
            job = definitions.get_job_def(spec["job_name"])
            nodes = sorted(job.graph.node_dict)
            edges = sorted(
                [dep.node.name, name]
                for name in nodes
                for deps in job.graph.dependency_structure.input_to_upstream_outputs_for_node(
                    name
                ).values()
                for dep in deps
            )
        # Config validation and plan creation are part of definition qualification.
        plan = create_execution_plan(job, run_config=spec["run_config"])
        report["definition"] = {
            "status": "pass",
            "nodes": nodes,
            "edges": edges,
            "planned_steps": plan.step_keys_to_execute,
        }
    except Exception:
        report["definition"] = {"status": "fail", "error": traceback.format_exc()}
    else:
        # Persist definition evidence even if execution later times out or is OOM-killed.
        Path("/evidence/runtime.json").write_text(json.dumps(report, indent=2))
        try:
            result = job.execute_in_process(run_config=spec["run_config"], raise_on_error=False)
            events = [
                {
                    "type": e.event_type_value,
                    "step_key": e.step_key,
                    "message": e.message,
                }
                for e in result.all_events
            ]
            checks = [
                {
                    "asset": e.event_specific_data.asset_key.to_user_string(),
                    "name": e.event_specific_data.check_name,
                    "passed": e.event_specific_data.passed,
                }
                for e in result.all_events
                if e.event_type_value == "ASSET_CHECK_EVALUATION"
            ]
            materialized = sorted(
                {
                    e.asset_key.to_user_string()
                    for e in result.all_events
                    if e.event_type_value == "ASSET_MATERIALIZATION"
                }
            )
            completed_steps = sorted(
                {e.step_key for e in result.all_events if e.event_type_value == "STEP_SUCCESS"}
            )
            covered = (
                set(materialized) >= set(nodes)
                if spec["mode"] == "assets"
                else set(completed_steps) >= set(plan.step_keys_to_execute)
            )
            report["execution"] = {
                "status": "pass"
                if result.success and covered and all(c["passed"] for c in checks)
                else "fail",
                "run_id": result.run_id,
                "run_success": result.success,
                "coverage": covered,
                "materialized": materialized,
                "completed_steps": completed_steps,
                "asset_checks": checks,
                "events": events,
            }
        except Exception:
            report["execution"] = {"status": "fail", "error": traceback.format_exc()}
    Path("/evidence/runtime.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
