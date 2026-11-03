from collections import Counter
import pickle
from app.control_compiler import plan_function, support_source, asset_name


def nested_reference(data, out):
    def inner(value):
        return Counter(value)

    return inner(data)


def test_globals_used_only_by_nested_functions_are_embedded():
    assert "Counter" in support_source(nested_reference)


def test_reserved_dagster_task_label_has_explicit_mapping():
    assert asset_name("context") == "context_features"


def guarded_reference(data, out):
    frame = data.read()
    for column in ["x"]:
        if frame[column].isna().any():
            raise ValueError("invalid")
    frame.to_csv(out / "a.csv")


def file_handles_reference(data, out):
    first = data.read()
    with (out / "a.pkl").open("wb") as handle:
        pickle.dump(first, handle)
    second = data.read()
    with (out / "b.pkl").open("wb") as handle:
        pickle.dump(second, handle)


def test_validation_inside_loops_is_preserved_in_data_lineage():
    plan = plan_function(guarded_reference, {"tasks": [{"id": "a", "outputs": ["a.csv"]}]})
    guard = next(s for s in plan["steps"] if s["source"].startswith("for column"))
    publication = next(s for s in plan["steps"] if s["outputs"])
    assert publication["dependencies"]["frame"] == guard["index"]


def test_context_manager_handle_is_not_a_cross_branch_dependency():
    plan = plan_function(
        file_handles_reference,
        {"tasks": [{"id": "a", "outputs": ["a.pkl"]}, {"id": "b", "outputs": ["b.pkl"]}]},
    )
    second = next(s for s in plan["steps"] if s["outputs"] == ["b.pkl"])
    assert "handle" not in second["dependencies"]


def reference(data, out):
    value = data.read()
    value.to_csv(out / "a.csv")
    branch = value.copy()
    branch.to_csv(out / "b.csv")
    branch = value.copy()
    branch.to_csv(out / "c.csv")


def test_branch_reassignment_does_not_create_hidden_previous_branch_dependency():
    graph = {"tasks": [{"id": name, "outputs": [name + ".csv"]} for name in ["a", "b", "c"]]}
    plan = plan_function(reference, graph)
    branch_assignments = [s for s in plan["steps"] if s["source"].startswith("branch =")]
    assert len(branch_assignments) == 2
    assert "branch" not in branch_assignments[1]["dependencies"]
    assert set(plan["targets"]) == {"a", "b", "c"}


def test_each_task_requires_an_observable_publication_checkpoint():
    import pytest

    with pytest.raises(ValueError, match="Unresolved artifact"):
        plan_function(reference, {"tasks": [{"id": "missing", "outputs": ["absent.csv"]}]})
