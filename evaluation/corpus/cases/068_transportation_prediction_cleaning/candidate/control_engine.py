"""Conservative statement/dataflow adapter for trusted behavioral references.

This is control preparation, never candidate repair or semantic RQ1 extraction.
Unsupported reference structures fail explicitly and require a handwritten adapter.
"""

import ast
import copy
import inspect
import textwrap


def root_name(node):
    while isinstance(node, (ast.Attribute, ast.Subscript)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def asset_name(name):
    return 'context_features' if name=='context' else name


def writes(statement):
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {statement.name}
    names = {
        n.id
        for n in ast.walk(statement)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
    }
    names -= {
        n.id
        for gen in ast.walk(statement)
        if isinstance(gen, ast.comprehension)
        for n in ast.walk(gen.target)
        if isinstance(n, ast.Name)
    }
    for node in ast.walk(statement):
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, ast.Store):
            names.add(root_name(node))
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "fit",
                "fit_transform",
                "insert",
                "update",
                "append",
                "extend",
                "sort",
                "fillna",
                "dropna",
                "rename",
                "replace",
            }:
                if node.func.attr in {
                    "fit",
                    "fit_transform",
                    "insert",
                    "update",
                    "append",
                    "extend",
                    "sort",
                } or any(
                    k.arg == "inplace" and isinstance(k.value, ast.Constant) and k.value.value
                    for k in node.keywords
                ):
                    names.add(root_name(node.func.value))
            if (
                isinstance(node.func, ast.Name)
                and node.func.id
                in {
                    "require",
                    "req",
                    "check",
                    "valid",
                    "prep",
                    "numeric",
                    "nums",
                    "finite",
                    "key",
                    "unique_nonblank",
                    "nonblank_unique",
                }
                and node.args
            ):
                names.add(root_name(node.args[0]))
    for guard in ast.walk(statement):
        if isinstance(guard, (ast.If, ast.Assert)):
            names.update(
                n.id
                for n in ast.walk(guard.test)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
            )
    return names - {None, "data", "out"}


def published(statement, artifacts):
    result = set()
    for node in ast.walk(statement):
        if isinstance(node, ast.Call):
            name = (
                node.func.attr
                if isinstance(node.func, ast.Attribute)
                else node.func.id
                if isinstance(node.func, ast.Name)
                else ""
            )
            if name in {"to_csv", "to_parquet", "write_text", "write_json", "js", "dump"}:
                result.update(
                    n.value
                    for n in ast.walk(node)
                    if isinstance(n, ast.Constant)
                    and isinstance(n.value, str)
                    and n.value in artifacts
                )
            if (
                name == "_classification"
                and len(node.args) >= 5
                and isinstance(node.args[4], ast.Constant)
            ):
                prefix = node.args[4].value
                result.update(a for a in artifacts if a.startswith(prefix + "_"))
        if isinstance(node, ast.With) and any(
            isinstance(n, ast.Constant) and n.value == "wb" for n in ast.walk(node)
        ):
            result.update(
                n.value
                for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in artifacts
            )
    return result


def plan_function(function, graph):
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    body = tree.body[0].body
    declared = {
        n.id
        for statement in body
        for n in ast.walk(statement)
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
    }
    declared.update(
        n.name for statement in body for n in ast.walk(statement) if isinstance(n, ast.FunctionDef)
    )
    owners = {a: t["id"] for t in graph["tasks"] for a in t["outputs"]}
    last = {}
    steps = []
    targets = {t["id"]: [] for t in graph["tasks"]}
    observed = set()
    for index, statement in enumerate(body):
        if isinstance(statement, ast.Return):
            continue
        outputs = published(statement, set(owners))
        tasks = {owners[a] for a in outputs}
        if len(tasks) > 1:
            raise ValueError(f"One compound statement publishes multiple logical tasks: {outputs}")
        loads = {
            n.id
            for n in ast.walk(statement)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
        }
        bound = {
            n.id
            for gen in ast.walk(statement)
            if isinstance(gen, ast.comprehension)
            for n in ast.walk(gen.target)
            if isinstance(n, ast.Name)
        }
        bound.update(
            a.arg
            for node in ast.walk(statement)
            if isinstance(node, (ast.Lambda, ast.FunctionDef))
            for a in node.args.args
        )
        bound.update(
            n.id
            for item in ast.walk(statement)
            if isinstance(item, ast.withitem) and item.optional_vars is not None
            for n in ast.walk(item.optional_vars)
            if isinstance(n, ast.Name)
        )
        loads -= bound
        if isinstance(statement, ast.AugAssign):
            loads.add(root_name(statement.target))
        updates = writes(statement) & declared
        dependencies = {name: last[name] for name in loads if name in last}
        source = ast.unparse(statement)
        steps.append(
            {
                "index": index,
                "source": source,
                "dependencies": dependencies,
                "writes": sorted(updates),
                "outputs": sorted(outputs),
            }
        )
        for name in updates:
            last[name] = index
        for task in tasks:
            targets[task].append(index)
        observed.update(outputs)
    missing = set(owners) - observed
    if missing:
        raise ValueError(f"Unresolved artifact publication checkpoints: {sorted(missing)}")
    if any(not indices for indices in targets.values()):
        raise ValueError("Task has no computational checkpoint")
    return {"steps": steps, "targets": targets}


def support_source(function):
    """Embed just the referenced imports/constants/helpers, not an entire pipeline replay."""
    imports = {}
    functions = {}
    constants = {}
    seen = {}

    def gather(fn):
        closure = inspect.getclosurevars(fn)
        values=dict(closure.globals)
        def nested_globals(code):
            for constant in code.co_consts:
                if inspect.iscode(constant):
                    for name in constant.co_names:
                        if name in fn.__globals__: values[name]=fn.__globals__[name]
                    nested_globals(constant)
        nested_globals(fn.__code__)
        for name, obj in values.items():
            if name in seen:
                if seen[name] is not obj and repr(seen[name]) != repr(obj):
                    raise ValueError(f"Conflicting helper global {name}")
                continue
            seen[name] = obj
            if inspect.ismodule(obj):
                imports[name] = f"import {obj.__name__} as {name}"
            elif inspect.isfunction(obj) and (
                obj.__module__.startswith("batch") or obj.__module__.startswith("<")
            ):
                gather(obj)
                functions[name] = textwrap.dedent(inspect.getsource(obj))
            elif inspect.isclass(obj) or inspect.isfunction(obj) or inspect.isbuiltin(obj):
                imports[name] = f"from {obj.__module__} import {obj.__name__} as {name}"
            elif name == "__file__":
                pass
            elif isinstance(obj, (str, int, float, bool, list, tuple, dict, set, type(None))):
                constants[name] = repr(obj)
            else:
                raise ValueError(f"Unsupported global {name}: {type(obj)}")

    gather(function)
    return (
        "\n".join(
            [*imports.values(), *[f"{k} = {v}" for k, v in constants.items()], *functions.values()]
        )
        + "\n"
    )


def build_definitions(graph, plan, globals_dict, data, out):
    import dagster as dg

    by_index = {s["index"]: s for s in plan["steps"]}
    dependencies = {
        t["id"]: [e["source"] for e in graph["dependencies"] if e["target"] == t["id"]]
        for t in graph["tasks"]
    }

    def factory(task):
        parents = [asset_name(p) for p in dependencies[task["id"]]]

        def run(**upstream):
            states = {}
            seen_artifacts = set()
            for payload in upstream.values():
                states.update(payload["states"])
                seen_artifacts.update(payload["artifacts"])
            required = {a for a in task["inputs"] if not a.startswith("input:")}
            if not required <= seen_artifacts:
                raise RuntimeError(
                    f"Missing current-run parent publications: {required - seen_artifacts}"
                )
            executed = []

            def compute(index):
                if index in states:
                    return
                step = by_index[index]
                if set(step["outputs"]) - set(task["outputs"]):
                    raise RuntimeError(
                        f"Hidden cross-task publication required by {task['id']}: {step['outputs']}"
                    )
                namespace = {**globals_dict, "data": data, "out": out}
                for name, dep in step["dependencies"].items():
                    compute(dep)
                    if name in states[dep]:
                        value = states[dep][name]
                        namespace[name] = (
                            value
                            if inspect.isfunction(value) or inspect.ismodule(value)
                            else copy.deepcopy(value)
                        )
                exec(
                    compile(step["source"], f"<control:{task['id']}:statement:{index}>", "exec"),
                    namespace,
                )
                states[index] = {
                    name: namespace[name] for name in step["writes"] if name in namespace
                }
                executed.append(index)

            for index in plan["targets"][task["id"]]:
                compute(index)
            for name in task["outputs"]:
                if not (out / name).is_file():
                    raise RuntimeError(f"Control did not publish {name}")
            seen_artifacts.update(task["outputs"])
            # Review trace exposes recomputation and actual reference statement slices.
            import json

            trace = out / "_control_trace"
            trace.mkdir(exist_ok=True)
            (trace / f"{task['id']}.json").write_text(
                json.dumps(
                    {
                        "task": task["id"],
                        "executed_statements": executed,
                        "declared_inputs": task["inputs"],
                        "outputs": task["outputs"],
                    }
                )
            )
            return {"states": states, "artifacts": seen_artifacts}

        return dg.asset(name=asset_name(task["id"]), ins={name: dg.AssetIn() for name in parents})(run)

    return dg.Definitions(
        assets=[factory(task) for task in graph["tasks"]],
        resources={"io_manager": dg.mem_io_manager},
        executor=dg.in_process_executor,
    )
