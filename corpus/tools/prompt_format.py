"""Render public task text and fixture headers without consulting reference graphs."""

import csv
import hashlib
import json
from pathlib import Path

VERSION = "servicecraft.task-prompt@2"
HEADINGS = (
    "1. Objective",
    "2. Available input files",
    "3. Required processing behavior",
    "4. Dependency and topology requirements",
    "5. Mandatory output artifacts",
    "6. Execution and numerical requirements",
    "7. Deliverable",
)


def render_prompt(source):
    source = Path(source)
    raw = (source / "description.md").read_bytes()
    description = raw.decode("utf-8").strip()
    title, separator, body = description.partition("\n\n")
    if not separator or not title.startswith("# "):
        raise ValueError(f"Expected a title and task body: {source.name}")
    behavior, separator, artifacts = body.partition("Mandatory output files:")
    if not separator or not artifacts.strip():
        raise ValueError(f"Missing mandatory output section: {source.name}")
    paragraphs = behavior.strip().split("\n\n")
    contracts = [p for p in paragraphs if p.startswith("Execution")]
    requirements = [p for p in paragraphs if not p.startswith("Execution")]
    if not requirements or not contracts:
        raise ValueError(f"Missing behavior or execution contract: {source.name}")

    inventory = []
    inputs = source / "inputs"
    for path in sorted(inputs.rglob("*")):
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(inputs.resolve()):
            raise ValueError("Input file escapes the public input directory")
        item = {"path": path.relative_to(source).as_posix()}
        if path.suffix.lower() == ".csv":
            with path.open(encoding="utf-8-sig", newline="") as stream:
                columns = next(csv.reader(stream), [])
            if not columns:
                raise ValueError(f"Empty input header: {path}")
            item["columns_present"] = columns
        inventory.append(item)
    if not inventory:
        raise ValueError(f"No public input files: {source.name}")
    input_lines = []
    for item in inventory:
        line = f"- {item['path']}"
        if "columns_present" in item:
            line += "\n  Columns present: " + ", ".join(item["columns_present"])
        input_lines.append(line)

    processing = "\n\n".join(requirements[1:]) or (
        "Apply all processing requirements in the objective above. Retain its "
        "specified transformations, parameters, validation policies and ordering."
    )
    sections = [
        requirements[0],
        "\n".join(input_lines) + "\n\nThese are available source columns, not a requirement "
        "to use every column. Follow the task-specific column-selection and validation "
        "rules below. Input paths are relative to the supplied generation workspace.",
        processing,
        "Preserve the logical ordering, data dependencies, independent branches and "
        "joins specified in the objective and processing requirements. Independent "
        "branches must not acquire dependencies on one another; joins must consume "
        "the required current-run upstream artifacts. Do not replace a required "
        "branched pipeline with a sequential chain or add a join between independent "
        "components. Logical task counts stated in the requirements describe required "
        "operations; any permitted alternative Dagster decomposition must preserve "
        "their behavior, topology and observable checkpoints.",
        artifacts.strip(),
        "\n\n".join(contracts),
        "Produce executable local Dagster source implementing this specification. "
        "Write every mandatory artifact beneath the run output directory supplied by "
        "the experiment harness. The shared runtime/submission contract supplies "
        "the entry point, paths, package versions and resource limits. Use those "
        "instructions together with this task prompt. No human corrections are "
        "available during a scored run.",
    ]
    prompt = title + "\n\n" + "\n\n".join(
        heading + "\n\n" + text for heading, text in zip(HEADINGS, sections)
    ) + "\n"
    # Preserve every original requirement paragraph, including output annotations.
    assert all(p in prompt for p in paragraphs)
    assert artifacts.strip() in prompt
    encoded = prompt.encode("utf-8")
    metadata = {
        "case_id": source.name,
        "description_sha256": hashlib.sha256(raw).hexdigest(),
        "input_inventory_sha256": hashlib.sha256(
            json.dumps(inventory, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "prompt_sha256": hashlib.sha256(encoded).hexdigest(),
    }
    return encoded, metadata
