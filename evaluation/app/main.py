"""Optional local operator API for the ServiceCraft evaluator."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from . import __version__
from .evaluator import evaluate

app = FastAPI(title="ServiceCraft Evaluation", version=__version__)


class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_path: str
    inputs_path: str
    spec_path: str
    report_dir: str
    metadata: dict = Field(default_factory=dict)


@app.get("/health")
def health():
    return {"status": "ok", "service": "servicecraft", "version": __version__}


@app.post("/evaluate")
def evaluate_submission(request: EvaluationRequest):
    """The experiment operator supplies private protocol and local filesystem paths."""
    try:
        return evaluate(
            Path(request.candidate_path),
            Path(request.inputs_path),
            Path(request.spec_path),
            Path(request.report_dir),
            request.metadata,
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
