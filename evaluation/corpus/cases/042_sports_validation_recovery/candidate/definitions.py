import json,os
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
