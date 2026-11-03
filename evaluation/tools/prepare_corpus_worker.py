"""Run inside the pinned image: prepare reference-derived stage controls, never admit them blindly."""

import json
import runpy
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/servicecraft")
from app.control_compiler import plan_function, support_source

ROOT = Path("/benchmark")
OUT = Path("/prepared")


def main():
    records = []
    for path in sorted((ROOT / "pipelines").glob("*/task_graph.json")):
        graph = json.loads(path.read_text())
        case = graph["pipeline_id"]
        dest = OUT / case
        dest.mkdir(exist_ok=True)
        if (dest / "inputs").exists():
            records.append({"case": case, "preparation": "existing", "review_status": "preserved"})
            continue
        shutil.copytree(path.parent / "inputs", dest / "inputs")
        candidate = dest / "candidate"
        candidate.mkdir()
        try:
            namespace = runpy.run_path(str(path.parent / "reference.py"))
            if "TASKS" in namespace:
                shutil.copyfile(path.parent / "reference.py", candidate / "native_reference.py")
                (candidate / "graph.json").write_text(json.dumps(graph))
                (candidate / "definitions.py").write_text("""import json,os
from pathlib import Path
import dagster as dg
import native_reference
root=Path(__file__).parent
graph=json.loads((root/'graph.json').read_text())
data=Path(os.environ['SERVICECRAFT_INPUT_DIR']);out=Path(os.environ['SERVICECRAFT_OUTPUT_DIR'])
def factory(task):
    parents=[e['source'] for e in graph['dependencies'] if e['target']==task['id']]
    def run(**upstream):
        native_reference.TASKS[task['id']](data,out)
        for artifact in task['outputs']:
            if not (out/artifact).is_file(): raise RuntimeError('Missing artifact '+artifact)
        return task['outputs']
    return dg.asset(name=task['id'],ins={p:dg.AssetIn() for p in parents})(run)
defs=dg.Definitions(assets=[factory(t) for t in graph['tasks']])
""")
                (dest / "task_graph.json").write_text(json.dumps(graph, indent=2))
                records.append(
                    {
                        "case": case,
                        "preparation": "prepared",
                        "review_status": "native_task_functions",
                    }
                )
                continue
            fn = namespace["RUNNERS"][case]
            plan = plan_function(fn, graph)
            (candidate / "support.py").write_text(support_source(fn))
            (candidate / "graph.json").write_text(json.dumps(graph, indent=2))
            (candidate / "plan.json").write_text(json.dumps(plan, indent=2))
            shutil.copyfile(
                "/servicecraft/app/control_compiler.py", candidate / "control_engine.py"
            )
            (candidate / "definitions.py").write_text(
                "import json, os\nfrom pathlib import Path\nimport support\nfrom control_engine import build_definitions\nroot=Path(__file__).parent\nsupport.__file__=str(root / "
                + repr(case)
                + ' / "reference.py")\ndefs=build_definitions(json.loads((root/"graph.json").read_text()),json.loads((root/"plan.json").read_text()),vars(support),Path(os.environ["SERVICECRAFT_INPUT_DIR"]),Path(os.environ["SERVICECRAFT_OUTPUT_DIR"]))\n'
            )
            (dest / "task_graph.json").write_text(json.dumps(graph, indent=2))
            records.append(
                {
                    "case": case,
                    "preparation": "prepared",
                    "review_status": "stage_mapping_requires_qualification",
                }
            )
        except Exception as exc:
            records.append(
                {
                    "case": case,
                    "preparation": "needs_adapter",
                    "error": str(exc),
                    "review_status": "not_admitted",
                }
            )
        print(json.dumps(records[-1]), flush=True)
    (OUT / "preparation.json").write_text(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
