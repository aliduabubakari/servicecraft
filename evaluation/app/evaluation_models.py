"""Versioned, evaluator-owned research protocol (never supplied by generated code)."""

import re
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Artifact(StrictModel):
    path: str
    format: Literal["csv", "json", "file"]
    required_columns: list[str] = Field(default_factory=list)
    required_keys: list[str] = Field(default_factory=list)
    min_rows: int = Field(default=0, ge=0)


class Oracle(StrictModel):
    id: str
    artifact: str
    kind: Literal["json_equals", "csv_equals"]
    # Reference paths are relative to the private evaluation specification.
    reference: str
    atol: float = Field(default=1e-6, ge=0)
    rtol: float = Field(default=1e-6, ge=0)


class ExternalOracle(StrictModel):
    id: str
    directory: str
    script: str = "check.py"
    image: str


class EvaluationSpec(StrictModel):
    schema_version: Literal["servicecraft.evaluation-spec@1"]
    case_id: str
    module: str
    attribute: str = "defs"
    project_dir: str = "."
    python_paths: list[str] = Field(default_factory=lambda: [".", "src"])
    # Optional bundle-relative mounts for exporters with fixed ../inputs/outputs paths.
    bundle_inputs: str | None = None
    bundle_outputs: str | None = None
    environment_aliases: dict[str, Literal["input_dir", "input_manifest", "output_dir"]] = Field(
        default_factory=dict
    )
    mode: Literal["assets", "job"] = "assets"
    job_name: str | None = None
    run_config: dict[str, Any] = Field(default_factory=dict)
    expected_nodes: list[str] = Field(min_length=1)
    expected_edges: list[tuple[str, str]] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(min_length=1)
    oracles: list[Oracle] = Field(min_length=1)
    external_oracles: list[ExternalOracle] = Field(default_factory=list)
    image: str = "servicecraft-runtime:1.13.12"
    timeout_seconds: int = Field(default=120, ge=1, le=3600)
    memory: str = "1g"
    cpus: float = Field(default=1.0, gt=0, le=16)
    required_packages: dict[str, str] = Field(default_factory=lambda: {"dagster": "1.13.12"})
    required_imports: list[str] = Field(default_factory=lambda: ["dagster"])

    @model_validator(mode="after")
    def coherent(self):
        if any(
            not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", alias) or alias.startswith("SERVICECRAFT_")
            for alias in self.environment_aliases
        ):
            raise ValueError(
                "Aliases must be valid environment names outside the reserved SERVICECRAFT_ namespace"
            )
        if self.mode == "job" and not self.job_name:
            raise ValueError("job mode requires job_name")
        if len(set(self.expected_nodes)) != len(self.expected_nodes):
            raise ValueError("duplicate expected nodes")
        if any(
            a not in self.expected_nodes or b not in self.expected_nodes
            for a, b in self.expected_edges
        ):
            raise ValueError("edge endpoint missing from expected_nodes")
        paths = [a.path for a in self.artifacts]
        if len(set(paths)) != len(paths) or len({o.id for o in self.oracles}) != len(self.oracles):
            raise ValueError("duplicate artifact path or oracle ID")
        if any(o.artifact not in paths for o in self.oracles):
            raise ValueError("oracle must reference a declared artifact")
        return self


class StageReport(BaseModel):
    model_config = ConfigDict(extra="allow")
    status: Literal["pass", "fail", "not_reached", "timeout", "infra_error"]


class EvaluationStages(StrictModel):
    submission: StageReport
    static: StageReport
    definition_graph: StageReport
    execution: StageReport
    contracts: StageReport
    oracle: StageReport


class BinaryScores(StrictModel):
    dagster_executable: Literal[0, 1] | None
    output_contract_valid: Literal[0, 1] | None
    behaviorally_correct: Literal[0, 1] | None
    complete_success: Literal[0, 1] | None


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: Literal["servicecraft.evaluation-result@1"]
    run_id: str
    metadata: dict[str, Any]
    stages: EvaluationStages
    scores: BinaryScores
    elapsed_seconds: float = Field(ge=0)

    @model_validator(mode="after")
    def verdict_matches_evidence(self):
        statuses = [s.status for s in self.stages.__dict__.values()]
        if "infra_error" in statuses:
            if any(v is not None for v in self.scores.__dict__.values()):
                raise ValueError("Infrastructure errors must have unavailable scores")
        elif self.scores.complete_success != int(all(s == "pass" for s in statuses)):
            raise ValueError("Complete success must agree with all six stages")
        return self
