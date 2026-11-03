"""Validate task graph shape, artifact bindings, provenance and DAG consistency."""
import hashlib
import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def topology_profile(task_ids, edges):
    """Return structural facts used to verify the declared topology class."""
    incoming={task:0 for task in task_ids};outgoing={task:0 for task in task_ids}
    neighbors={task:set() for task in task_ids}
    for source,target in edges:
        outgoing[source]+=1;incoming[target]+=1
        neighbors[source].add(target);neighbors[target].add(source)
    components=[];unseen=set(task_ids)
    while unseen:
        seed=next(iter(unseen));stack=[seed];component=set()
        while stack:
            node=stack.pop()
            if node in component:continue
            component.add(node);unseen.discard(node);stack.extend(neighbors[node]-component)
        components.append(component)
    return {'incoming':incoming,'outgoing':outgoing,'components':components,
            'roots':[task for task in task_ids if incoming[task]==0],
            'sinks':[task for task in task_ids if outgoing[task]==0],
            'joins':[task for task in task_ids if incoming[task]>1],
            'splits':[task for task in task_ids if outgoing[task]>1]}


def validate_topology(label, task_ids, edges):
    profile=topology_profile(task_ids,edges)
    incoming=profile['incoming'];outgoing=profile['outgoing']
    connected=len(profile['components'])==1
    joins=profile['joins'];splits=profile['splits']
    if label=='linear':
        valid=connected and len(edges)==len(task_ids)-1 and len(profile['roots'])==len(profile['sinks'])==1 and not joins and not splits
    elif label=='parallel':
        valid=len(profile['components'])>=2 and not joins and not splits and all(sum(1 for edge in edges if edge[0] in component and edge[1] in component)==len(component)-1 for component in profile['components'])
    elif label=='fan_in':
        valid=connected and bool(joins) and not splits and all(outgoing[node]==0 for node in joins)
    elif label=='fan_out':
        valid=connected and bool(splits) and not joins and all(incoming[node]==0 for node in splits)
    elif label=='fan_in_fan_out':
        valid=connected and bool(joins) and bool(splits)
    elif label=='linear_to_fan_in':
        valid=connected and bool(joins) and not splits and any(outgoing[node]>0 for node in joins)
    elif label=='linear_to_fan_out':
        valid=connected and bool(splits) and not joins and any(incoming[node]>0 for node in splits)
    else:
        valid=False
    assert valid, f"Declared topology {label!r} does not match graph structure: roots={profile['roots']}, sinks={profile['sinks']}, joins={joins}, splits={splits}, components={len(profile['components'])}"
    return {key:len(profile[key]) for key in ['components','roots','sinks','joins','splits']}

def validate(graph, directory=None):
    schema=json.loads((ROOT/'task-graph.schema.json').read_text())
    jsonschema.Draft202012Validator(schema).validate(graph)
    tasks={t['id']:t for t in graph['tasks']}
    assert len(tasks)==len(graph['tasks']), 'Duplicate task IDs'
    inputs={i['id'] for i in graph['inputs']}
    artifacts={a['id'] for a in graph['artifacts']}
    assert len(inputs)==len(graph['inputs']) and len(artifacts)==len(graph['artifacts']), 'Duplicate artifact/input IDs'
    assert not inputs & artifacts, 'Input and output IDs overlap'
    producers={}
    for t in tasks.values():
        for output in t['outputs']:
            assert output in artifacts and output not in producers, 'Missing/duplicate output producer'
            producers[output]=t['id']
    assert set(producers)==artifacts, 'Unproduced artifact'
    expected={}
    for t in tasks.values():
        for input in t['inputs']:
            assert input in inputs or input in producers, 'Unresolved task input'
            if input in producers:
                parent=producers[input]
                assert parent!=t['id'], 'Self dependency'
                expected.setdefault((parent,t['id']),set()).add(input)
    actual={}
    for d in graph['dependencies']:
        assert d['source'] in tasks and d['target'] in tasks, 'Unknown dependency endpoint'
        key=d['source'],d['target']
        assert key not in actual, 'Duplicate dependency'
        actual[key]=set(d['artifacts'])
    assert actual==expected, 'Dependency edges do not match artifact bindings'
    pending=set(tasks);done=set()
    while pending:
        ready={t for t in pending if all(parent in done for parent,target in actual if target==t)}
        assert ready, 'Cyclic graph'
        done |= ready;pending -= ready
    topology=validate_topology(graph['topology'],set(tasks),set(actual))
    if directory:
        provenance=json.loads((directory/'provenance.json').read_text())
        for item in graph['inputs']:
            path=(directory/item['path']).resolve()
            assert path.is_relative_to(directory.resolve()) and path.is_file(), 'Invalid input path'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==provenance['pilot_input_sha256'][path.name], 'Input hash mismatch'
        for a in graph['artifacts']:
            assert a['path'] in (directory/'description.md').read_text(), 'Output missing from description'
    return {'pipeline_id':graph['pipeline_id'],'topology':graph['topology'],'tasks':len(tasks),'dependencies':len(actual),'structure':topology,'status':'passed'}

if __name__=='__main__':
    for path in sorted((ROOT/'pipelines').glob('*/task_graph.json')):
        print(json.dumps(validate(json.loads(path.read_text()),path.parent)))
