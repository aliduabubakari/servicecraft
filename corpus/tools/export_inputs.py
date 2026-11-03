"""Create generator inputs using an allowlist. Never expose evaluator files by default."""
import argparse
import json
import shutil
from pathlib import Path

from prompt_format import render_prompt
ROOT=Path(__file__).resolve().parents[1]

def export(pipeline_id, destination, track):
    source=ROOT/'pipelines'/pipeline_id
    if not source.is_dir() or source.resolve().parent != (ROOT/'pipelines').resolve():
        raise ValueError('Unknown pipeline ID')
    graph=json.loads((source/'task_graph.json').read_text())
    prompt=(source/'prompt.txt').read_bytes()
    if prompt != render_prompt(source)[0]:
        raise ValueError('Stale prompt.txt; run tools/sync_prompts.py before exporting')
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    (destination/'prompt.txt').write_bytes(prompt)
    shutil.copyfile(source/'description.md',destination/'description.md')
    (destination/'inputs').mkdir()
    for item in graph['inputs']:
        path=(source/item['path']).resolve()
        if not path.is_relative_to((source/'inputs').resolve()):
            raise ValueError('Input path escapes inputs directory')
        shutil.copyfile(path,destination/'inputs'/path.name)
    if track=='fixed_graph':
        allowed=['schema_version','pipeline_id','title','inputs','tasks','artifacts','dependencies','numeric_tolerance']
        (destination/'provided_graph.json').write_text(json.dumps({k:graph[k] for k in allowed},indent=2)+'\n')
    return destination

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('pipeline_id')
    parser.add_argument('destination',type=Path)
    parser.add_argument('--track',choices=['natural_language','fixed_graph'],default='natural_language')
    args=parser.parse_args()
    print(export(args.pipeline_id,args.destination,args.track))
