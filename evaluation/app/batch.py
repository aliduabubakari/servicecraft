"""Frozen batch manifests, case controls, resumable attempts and analysis exports."""

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .evaluation_models import StrictModel, EvaluationSpec, EvaluationResult
from .evaluator import evaluate, hashes, strict_json, contained


class Profile(StrictModel):
    image: str
    required_packages: dict[str, str] = Field(min_length=1)
    required_imports: list[str] = Field(min_length=1)


class Submission(StrictModel):
    candidate: str
    inputs: str
    spec: str
    metadata: dict = Field(default_factory=dict)


class Control(Submission):
    profile: str


class Entry(Submission):
    id: str
    control: str


class Experiment(StrictModel):
    schema_version: Literal["servicecraft.experiment@1"]
    profiles: dict[str, Profile]
    controls: dict[str, Control]
    entries: list[Entry] = Field(min_length=1)
    infrastructure_retries: int = Field(default=0, ge=0, le=3)

    @model_validator(mode="after")
    def coherent(self):
        identifiers = list(self.controls) + [e.id for e in self.entries]
        if any(not re.fullmatch(r"[A-Za-z0-9_-]+", s) for s in identifiers):
            raise ValueError("Control and entry IDs must be safe directory identifiers")
        if len({e.id for e in self.entries}) != len(self.entries):
            raise ValueError("Duplicate entry IDs")
        if any(c.profile not in self.profiles for c in self.controls.values()) or any(
            e.control not in self.controls for e in self.entries
        ):
            raise ValueError("Unresolved control/profile")
        return self


def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def run_batch(manifest: Path, output: Path, *, resume=False):
    manifest, output = manifest.resolve(), output.resolve()
    protocol = Experiment.model_validate(strict_json(manifest))
    base = manifest.parent
    lock = {
        "manifest": protocol.model_dump(),
        "profiles": {},
        "sources": {},
        "evaluator_sources": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path(__file__).parent.glob("*.py")
        },
    }
    for name, profile in protocol.profiles.items():
        image = json.loads(
            subprocess.check_output(["docker", "image", "inspect", profile.image], timeout=30)
        )[0]
        lock["profiles"][name] = {**profile.model_dump(), "image": image["Id"]}
    for kind, name, sub in [("control", n, s) for n, s in protocol.controls.items()] + [
        ("entry", e.id, e) for e in protocol.entries
    ]:
        candidate, inputs, spec_path = [
            (base / p).resolve() for p in (sub.candidate, sub.inputs, sub.spec)
        ]
        if output.is_relative_to(candidate) or output.is_relative_to(inputs):
            raise ValueError("Batch output must be outside candidates and inputs")
        spec = EvaluationSpec.model_validate(strict_json(spec_path))
        refs = {
            o.reference: hashlib.sha256((spec_path.parent / o.reference).read_bytes()).hexdigest()
            for o in spec.oracles
        }
        external = []
        for oracle in spec.external_oracles:
            context = contained(spec_path.parent, oracle.directory)
            image = json.loads(
                subprocess.check_output(["docker", "image", "inspect", oracle.image], timeout=30)
            )[0]
            refs[f"external:{oracle.id}"] = {"context": hashes(context), "image": image["Id"]}
            external.append({**oracle.model_dump(), "image": image["Id"]})
        lock["sources"][f"{kind}/{name}"] = {
            "candidate": hashes(candidate),
            "inputs": hashes(inputs),
            "spec": spec.model_dump(),
            "references": refs,
            "external_oracles": external,
        }
    for entry in protocol.entries:
        c, e = lock["sources"][f"control/{entry.control}"], lock["sources"][f"entry/{entry.id}"]
        if c["spec"]["case_id"] != e["spec"]["case_id"] or c["inputs"] != e["inputs"]:
            raise ValueError(f"{entry.id}: control must qualify the same case and input fixture")
    if resume:
        if strict_json(output / "experiment-lock.json") != lock:
            raise ValueError(
                "Resume rejected: manifest, image, code, inputs or private references changed"
            )
    else:
        output.mkdir(parents=True, exist_ok=False)
        save(output / "experiment-lock.json", lock)

    def execute(sub, folder, profile, fingerprint):
        profile = {**profile, "external_oracles": fingerprint["external_oracles"]}
        for attempt in range(protocol.infrastructure_retries + 1):
            path = folder / f"try-{attempt:02d}"
            if (path / "result.json").is_file():
                result = strict_json(path / "result.json")
                EvaluationResult.model_validate(result)
            else:
                # An interrupted attempt is retained; never overwrite its partial evidence.
                if path.exists():
                    suffix = 0
                    while path.with_name(path.name + f"-interrupted-{suffix}").exists():
                        suffix += 1
                    path.rename(path.with_name(path.name + f"-interrupted-{suffix}"))
                result = evaluate(
                    *[(base / p).resolve() for p in (sub.candidate, sub.inputs, sub.spec)],
                    path,
                    {**sub.metadata, "infrastructure_try": attempt},
                    runtime_profile=profile,
                )
            if result["scores"]["complete_success"] is not None:
                return result, path
        return result, path

    controls = {}
    for name, control in protocol.controls.items():
        controls[name], _ = execute(
            control,
            output / "controls" / name,
            lock["profiles"][control.profile],
            lock["sources"][f"control/{name}"],
        )
    rows = []
    for entry in protocol.entries:
        control = protocol.controls[entry.control]
        if controls[entry.control]["scores"]["complete_success"] != 1:
            row = {
                "id": entry.id,
                "status": "blocked_control",
                "scores": {
                    k: None
                    for k in (
                        "dagster_executable",
                        "output_contract_valid",
                        "behaviorally_correct",
                        "complete_success",
                    )
                },
                "metadata": entry.metadata,
            }
        else:
            result, path = execute(
                entry,
                output / "entries" / entry.id,
                lock["profiles"][control.profile],
                lock["sources"][f"entry/{entry.id}"],
            )
            row = {
                "id": entry.id,
                "status": "infra_error"
                if result["scores"]["complete_success"] is None
                else "evaluated",
                "scores": result["scores"],
                "metadata": entry.metadata,
                "report": str(path.relative_to(output)),
                "stages": {s: v["status"] for s, v in result["stages"].items()},
                "static_metrics": result["stages"]["static"].get("scaled_metrics", {}),
            }
        rows.append(row)
        save(
            output / "summary.json",
            {
                "schema_version": "servicecraft.batch-result@1",
                "entries": rows,
                "scheduled": len(protocol.entries),
                "processed": len(rows),
            },
        )
    # No excluded rows: blocked and infrastructure attempts remain explicit.
    with (output / "results.jsonl").open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    with (output / "results.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "status",
                "dagster_executable",
                "output_contract_valid",
                "behaviorally_correct",
                "complete_success",
                "metadata",
                "report",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "id": row["id"],
                    "status": row["status"],
                    **row["scores"],
                    "metadata": json.dumps(row["metadata"]),
                    "report": row.get("report", ""),
                }
            )
    return {
        "entries": rows,
        "scheduled": len(rows),
        "complete_successes": sum(r["scores"]["complete_success"] == 1 for r in rows),
        "unavailable": sum(r["scores"]["complete_success"] is None for r in rows),
    }
