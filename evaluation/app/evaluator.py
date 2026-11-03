"""Six-stage research evaluator. Private assertions stay outside candidate containers."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

from .evaluation_models import EvaluationSpec, EvaluationResult
from . import __version__

STAGES = (
    "submission",
    "static",
    "definition_graph",
    "execution",
    "contracts",
    "oracle",
)
MAX_FILE_BYTES = 32 * 1024 * 1024


def contained(root: Path, relative: str, *, exists: bool = True) -> Path:
    root = root.resolve()
    path = root / relative
    if Path(relative).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes allowed root: {relative}")
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p.is_relative_to(root)):
        raise ValueError(f"Symlinks are not accepted: {relative}")
    if exists and not path.exists():
        raise ValueError(f"Missing path: {relative}")
    return path


def strict_json(path: Path):
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"Oversized JSON: {path.name}")
    return json.loads(
        path.read_text(),
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON: {value}")),
    )


def hashes(root: Path) -> dict:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def docker_run(
    image: str,
    mounts: list[tuple[Path, str, bool]],
    command: list[str],
    limits: EvaluationSpec,
    log: Path,
    *,
    workdir="/tmp",
) -> dict:
    """Container creation failures are infrastructure; candidate exit/timeouts are failures."""
    args = [
        "docker",
        "create",
        "--network=none",
        "--read-only",
        "--user=65532:65532",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--pids-limit=128",
        f"--memory={limits.memory}",
        f"--cpus={limits.cpus}",
        "--tmpfs=/tmp:rw,nosuid,size=512m",
        f"--workdir={workdir}",
    ]
    for host, target, readonly in mounts:
        args.extend(
            [
                "--mount",
                f"type=bind,source={host},target={target}" + (",readonly" if readonly else ""),
            ]
        )
    args.extend([image, *command])
    container = None
    start = time.monotonic()
    try:
        created = subprocess.run(args, capture_output=True, text=True, timeout=30)
        if created.returncode:
            return {"status": "infra_error", "error": created.stderr}
        container = created.stdout.strip()
        with log.open("w") as output:
            try:
                subprocess.run(
                    ["docker", "start", "--attach", container],
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    timeout=limits.timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                subprocess.run(["docker", "kill", container], capture_output=True, timeout=15)
                return {
                    "status": "timeout",
                    "elapsed_seconds": time.monotonic() - start,
                }
        inspected = json.loads(
            subprocess.check_output(["docker", "inspect", container], timeout=15)
        )[0]
        state = inspected["State"]
        ok = (
            state["ExitCode"] == 0
            and not state.get("OOMKilled")
            and not state.get("StartedAt", "0001").startswith("0001")
        )
        return {
            "status": "pass" if ok else "fail",
            "exit_code": state["ExitCode"],
            "oom_killed": state.get("OOMKilled"),
            "elapsed_seconds": time.monotonic() - start,
            "image_id": inspected["Image"],
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "infra_error", "error": str(exc)}
    finally:
        if container:
            try:
                subprocess.run(
                    ["docker", "rm", "--force", container], capture_output=True, timeout=20
                )
            except (OSError, subprocess.SubprocessError):
                pass


def graph_score(actual: dict, spec: EvaluationSpec) -> dict:
    expected_nodes, actual_nodes = set(spec.expected_nodes), set(actual["nodes"])
    expected_edges, actual_edges = (
        set(spec.expected_edges),
        {tuple(e) for e in actual["edges"]},
    )
    requirements = len(expected_nodes) + len(expected_edges)
    correct = len(expected_nodes & actual_nodes) + len(expected_edges & actual_edges)
    return {
        "status": "pass"
        if actual_nodes == expected_nodes and actual_edges == expected_edges
        else "fail",
        "structure_score_01": correct
        / (requirements + len(actual_nodes - expected_nodes) + len(actual_edges - expected_edges)),
        "missing_nodes": sorted(expected_nodes - actual_nodes),
        "unexpected_nodes": sorted(actual_nodes - expected_nodes),
        "missing_edges": sorted(expected_edges - actual_edges),
        "unexpected_edges": sorted(actual_edges - expected_edges),
        "actual": actual,
    }


def check_contracts(outputs: Path, spec: EvaluationSpec) -> dict:
    checks = []
    for artifact in spec.artifacts:
        try:
            path = contained(outputs, artifact.path)
            if not path.is_file() or not 0 < path.stat().st_size <= MAX_FILE_BYTES:
                raise ValueError("Artifact must be a nonempty regular file within size limit")
            if artifact.format == "json":
                payload = strict_json(path)
                if artifact.required_keys and (
                    not isinstance(payload, dict)
                    or not set(artifact.required_keys) <= payload.keys()
                ):
                    raise ValueError("Required JSON keys missing")
            elif artifact.format == "csv":
                with path.open(newline="") as handle:
                    reader = csv.DictReader(handle)
                    if not set(artifact.required_columns) <= set(reader.fieldnames or []):
                        raise ValueError("Required CSV columns missing")
                    rows = list(reader)
                    if len(rows) < artifact.min_rows or any(None in row for row in rows):
                        raise ValueError("CSV row count/shape mismatch")
            checks.append(
                {
                    "artifact": artifact.path,
                    "status": "pass",
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        except (ValueError, OSError, csv.Error) as exc:
            checks.append({"artifact": artifact.path, "status": "fail", "error": str(exc)})
    return {
        "status": "pass" if all(c["status"] == "pass" for c in checks) else "fail",
        "checks": checks,
    }


def equivalent(actual, expected, atol, rtol):
    if isinstance(expected, bool) or expected is None:
        return type(actual) is type(expected) and actual == expected
    if isinstance(expected, (int, float)):
        return (
            isinstance(actual, (int, float))
            and not isinstance(actual, bool)
            and math.isfinite(actual)
            and math.isfinite(expected)
            and abs(actual - expected) <= atol + rtol * abs(expected)
        )
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(equivalent(actual[k], v, atol, rtol) for k, v in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(equivalent(a, e, atol, rtol) for a, e in zip(actual, expected))
        )
    return type(actual) is type(expected) and actual == expected


def check_oracles(outputs: Path, private_root: Path, spec: EvaluationSpec) -> dict:
    checks = []
    for oracle in spec.oracles:
        try:
            actual_path, expected_path = (
                contained(outputs, oracle.artifact),
                contained(private_root, oracle.reference),
            )
            if max(actual_path.stat().st_size, expected_path.stat().st_size) > MAX_FILE_BYTES:
                raise ValueError("Oracle artifact too large")
            if oracle.kind == "json_equals":
                success = equivalent(
                    strict_json(actual_path),
                    strict_json(expected_path),
                    oracle.atol,
                    oracle.rtol,
                )
            else:
                with (
                    actual_path.open(newline="") as a,
                    expected_path.open(newline="") as e,
                ):
                    ar, er = csv.DictReader(a), csv.DictReader(e)
                    columns_match = ar.fieldnames == er.fieldnames
                    actual, expected = list(ar), list(er)

                def cell(v):
                    try:
                        return float(v)
                    except (TypeError, ValueError):
                        return v

                success = columns_match and equivalent(
                    [{k: cell(v) for k, v in row.items()} for row in actual],
                    [{k: cell(v) for k, v in row.items()} for row in expected],
                    oracle.atol,
                    oracle.rtol,
                )
            checks.append(
                {
                    "id": oracle.id,
                    "status": "pass" if success else "fail",
                    "reference_sha256": hashlib.sha256(expected_path.read_bytes()).hexdigest(),
                }
            )
        except (ValueError, OSError, csv.Error) as exc:
            checks.append({"id": oracle.id, "status": "fail", "error": str(exc)})
    return {
        "status": "pass" if checks and all(c["status"] == "pass" for c in checks) else "fail",
        "checks": checks,
    }


def evaluate(
    candidate: Path,
    inputs: Path,
    spec_path: Path,
    report_dir: Path,
    metadata: dict | None = None,
    *,
    runtime_profile: dict | None = None,
) -> dict:
    """Reports must be a fresh directory outside all mounted candidate/input trees."""
    candidate, inputs, spec_path, report_dir = (
        p.resolve() for p in (candidate, inputs, spec_path, report_dir)
    )
    if report_dir.is_relative_to(candidate) or report_dir.is_relative_to(inputs):
        raise ValueError("Report directory must be outside candidate and inputs")
    report_dir.mkdir(parents=True, exist_ok=False)
    report = {
        "schema_version": "servicecraft.evaluation-result@1",
        "evaluator_version": __version__,
        "run_id": str(uuid.uuid4()),
        "metadata": metadata or {},
        "stages": {s: {"status": "not_reached"} for s in STAGES},
        "scores": {
            "dagster_executable": 0,
            "output_contract_valid": 0,
            "behaviorally_correct": 0,
            "complete_success": 0,
        },
    }
    stages = report["stages"]
    started = time.monotonic()
    try:
        try:
            spec = EvaluationSpec.model_validate(strict_json(spec_path))
            if runtime_profile is not None:
                spec = EvaluationSpec.model_validate({**spec.model_dump(), **runtime_profile})
            for private_path in [
                spec_path,
                *(contained(spec_path.parent, o.reference) for o in spec.oracles),
            ]:
                if private_path.is_relative_to(candidate) or private_path.is_relative_to(inputs):
                    raise ValueError(
                        "Private evaluation files must be outside candidate and inputs"
                    )
            for oracle in spec.oracles:
                if oracle.kind == "json_equals":
                    strict_json(contained(spec_path.parent, oracle.reference))
            for oracle in spec.external_oracles:
                directory = contained(spec_path.parent, oracle.directory)
                contained(directory, oracle.script)
                if directory.is_relative_to(candidate) or directory.is_relative_to(inputs):
                    raise ValueError(
                        "Private oracle context must be outside generated code and inputs"
                    )
        except (ValueError, OSError) as exc:
            stages["submission"] = {
                "status": "infra_error",
                "error": f"Invalid evaluator protocol: {exc}",
            }
            return report
        report["case_id"] = spec.case_id
        report["spec_sha256"] = hashlib.sha256(spec_path.read_bytes()).hexdigest()
        report["protocol"] = spec.model_dump()
        if not inputs.is_dir():
            stages["submission"] = {
                "status": "infra_error",
                "error": "Benchmark inputs directory missing",
            }
            return report
        if not candidate.is_dir():
            raise ValueError("Candidate directory missing")
        for root in (candidate, inputs):
            for p in root.rglob("*"):
                contained(root, str(p.relative_to(root)))
                if not p.is_file() and not p.is_dir():
                    raise ValueError("Only regular files and directories accepted")
        contained(candidate, spec.project_dir)
        for p in spec.python_paths:
            contained(candidate, p, exists=False)
        if not list(candidate.rglob("*.py")):
            raise ValueError("No Python sources in submission")
        for artifact in spec.artifacts:
            contained(report_dir, artifact.path, exists=False)
        for mount in (spec.bundle_inputs, spec.bundle_outputs):
            if mount is not None:
                if mount in ("", "."):
                    raise ValueError("Bundle mounts must name subdirectories")
                if not contained(candidate, mount).is_dir():
                    raise ValueError("Bundle mount targets must be existing directories")
        # Freeze the resolved image for all phases, even if a mutable tag changes.
        try:
            image = json.loads(
                subprocess.check_output(["docker", "image", "inspect", spec.image], timeout=30)
            )[0]
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            stages["static"] = {"status": "infra_error", "error": str(exc)}
            return report
        image_id = image["Id"]
        report["runtime_image"] = {
            "id": image_id,
            "os": image["Os"],
            "architecture": image["Architecture"],
            "repo_digests": image.get("RepoDigests", []),
        }
        try:
            pinned = []
            for oracle in spec.external_oracles:
                oracle_image = json.loads(
                    subprocess.check_output(
                        ["docker", "image", "inspect", oracle.image], timeout=30
                    )
                )[0]
                pinned.append(oracle.model_copy(update={"image": oracle_image["Id"]}))
            spec = spec.model_copy(update={"external_oracles": pinned})
            report["protocol"] = spec.model_dump()
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            stages["oracle"] = {
                "status": "infra_error",
                "error": f"Oracle runtime unavailable: {exc}",
            }
            return report
        report["candidate_sha256"] = hashes(candidate)
        report["input_sha256"] = hashes(inputs)
        stages["submission"] = {"status": "pass"}
        with tempfile.TemporaryDirectory(prefix="servicecraft-eval-") as temp:
            scratch = Path(temp)
            # Snapshot inputs and sources so simultaneous editing cannot alter a run.
            candidate_snapshot, inputs_snapshot = (
                scratch / "candidate",
                scratch / "inputs",
            )
            shutil.copytree(candidate, candidate_snapshot)
            shutil.copytree(inputs, inputs_snapshot)
            if (
                hashes(candidate_snapshot) != report["candidate_sha256"]
                or hashes(inputs_snapshot) != report["input_sha256"]
            ):
                raise ValueError("Submission changed during snapshot")
            protocol, outputs, evidence = (scratch / n for n in ("protocol", "outputs", "evidence"))
            for p in (protocol, outputs, evidence):
                p.mkdir(mode=0o777)
                p.chmod(0o777)
            runtime_keys = (
                "module",
                "attribute",
                "project_dir",
                "python_paths",
                "mode",
                "job_name",
                "run_config",
                "environment_aliases",
                "required_packages",
                "required_imports",
            )
            (protocol / "runtime.json").write_text(
                json.dumps({k: spec.model_dump()[k] for k in runtime_keys})
            )
            shutil.copyfile(
                Path(__file__).with_name("environment_check.py"), protocol / "environment_check.py"
            )
            mounts = [
                (candidate_snapshot, "/candidate", True),
                (inputs_snapshot, "/inputs", True),
                (protocol, "/protocol", True),
                (outputs, "/outputs", False),
                (evidence, "/evidence", False),
            ]
            if spec.bundle_inputs:
                mounts.append((inputs_snapshot, f"/candidate/{spec.bundle_inputs}", True))
            if spec.bundle_outputs:
                mounts.append((outputs, f"/candidate/{spec.bundle_outputs}", False))
            preflight = docker_run(
                image_id,
                mounts,
                ["python", "/protocol/environment_check.py"],
                spec,
                report_dir / "environment.log",
            )
            report["environment"] = (
                strict_json(evidence / "environment.json")
                if preflight["status"] == "pass" and (evidence / "environment.json").is_file()
                else {"status": "infra_error", "container": preflight}
            )
            if report["environment"]["status"] != "pass":
                stages["submission"] = {
                    "status": "infra_error",
                    "error": "Approved runtime environment failed preflight",
                }
                return report
            static_cmd = [
                "python",
                "-c",
                "import sys,json;sys.path.insert(0,'/opt/evaluator');from static_analysis import analyze;from pathlib import Path;Path('/evidence/static.json').write_text(json.dumps(analyze(Path('/candidate'))))",
            ]
            static_run = docker_run(image_id, mounts, static_cmd, spec, report_dir / "static.log")
            if static_run["status"] == "pass" and (evidence / "static.json").is_file():
                stages["static"] = strict_json(evidence / "static.json")
                stages["static"]["container"] = static_run
            else:
                stages["static"] = (
                    static_run
                    if static_run["status"] != "pass"
                    else {"status": "infra_error", "error": "Missing static evidence"}
                )
            if stages["static"]["status"] != "pass":
                return report
            if any(t["status"] != "pass" for t in stages["static"]["tools"].values()):
                stages["static"]["status"] = "infra_error"
                return report
            runtime = docker_run(
                image_id,
                mounts,
                ["python", "/opt/evaluator/runtime_worker.py"],
                spec,
                report_dir / "runtime.log",
            )
            stages["execution"] = runtime
            if runtime["status"] != "infra_error" and (evidence / "runtime.json").is_file():
                data = strict_json(evidence / "runtime.json")
                (report_dir / "runtime-evidence.json").write_text(json.dumps(data, indent=2))
                definition = data["definition"]
                stages["definition_graph"] = (
                    graph_score(definition, spec) if definition["status"] == "pass" else definition
                )
                stages["execution"] = (
                    {**data["execution"], "container": runtime}
                    if runtime["status"] == "pass"
                    else runtime
                )
            elif runtime["status"] == "pass":
                stages["execution"] = {
                    "status": "fail",
                    "error": "Missing runtime evidence",
                }
            report["scores"]["dagster_executable"] = int(stages["execution"]["status"] == "pass")
            if stages["execution"]["status"] == "pass":
                stages["contracts"] = check_contracts(outputs, spec)
                stages["oracle"] = check_oracles(outputs, spec_path.parent, spec)
                for index, oracle in enumerate(spec.external_oracles):
                    oracle_evidence = scratch / f"oracle-evidence-{index}"
                    oracle_evidence.mkdir(mode=0o777)
                    oracle_evidence.chmod(0o777)
                    context = contained(spec_path.parent, oracle.directory)
                    oracle_run = docker_run(
                        oracle.image,
                        [
                            (context, "/oracle", True),
                            (inputs_snapshot, "/inputs", True),
                            (outputs, "/outputs", True),
                            (oracle_evidence, "/evidence", False),
                        ],
                        ["python", f"/oracle/{oracle.script}"],
                        spec,
                        report_dir / f"oracle-{index}.log",
                    )
                    if (
                        oracle_run["status"] == "pass"
                        and (oracle_evidence / "oracle.json").is_file()
                    ):
                        detail = strict_json(oracle_evidence / "oracle.json")
                        detail["id"] = oracle.id
                        detail["container"] = oracle_run
                    else:
                        detail = {"id": oracle.id, "status": "infra_error", "container": oracle_run}
                    stages["oracle"].setdefault("external", []).append(detail)
                    if (
                        detail["status"] == "infra_error"
                        or stages["oracle"]["status"] == "infra_error"
                    ):
                        stages["oracle"]["status"] = "infra_error"
                    elif detail["status"] != "pass":
                        stages["oracle"]["status"] = "fail"
                report["scores"]["output_contract_valid"] = int(
                    stages["contracts"]["status"] == "pass"
                )
                report["scores"]["behaviorally_correct"] = int(stages["oracle"]["status"] == "pass")
                # Copy only evaluator-declared, checked regular output files.
                for artifact in spec.artifacts:
                    try:
                        src = contained(outputs, artifact.path)
                        if src.is_file() and src.stat().st_size <= MAX_FILE_BYTES:
                            dest = report_dir / "artifacts" / artifact.path
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copyfile(src, dest)
                    except ValueError:
                        pass
            report["scores"]["complete_success"] = int(
                all(stages[s]["status"] == "pass" for s in STAGES)
            )
    except (ValueError, OSError) as exc:
        stage = (
            "submission"
            if stages["submission"]["status"] != "pass"
            else next((s for s in STAGES if stages[s]["status"] == "not_reached"), "execution")
        )
        stages[stage] = {"status": "fail", "error": str(exc)}
    except Exception as exc:
        stages["execution"] = {
            "status": "infra_error",
            "error": f"Evaluator error: {type(exc).__name__}: {exc}",
        }
    finally:
        report["elapsed_seconds"] = time.monotonic() - started
        if any(s["status"] == "infra_error" for s in stages.values()):
            report["scores"] = {k: None for k in report["scores"]}
        EvaluationResult.model_validate(report)
        temporary = report_dir / "result.json.tmp"
        temporary.write_text(json.dumps(report, indent=2))
        temporary.replace(report_dir / "result.json")
    return report
