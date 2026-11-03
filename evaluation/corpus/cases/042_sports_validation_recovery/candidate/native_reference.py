"""Reviewed pilot reference. Run --help for CLI; no network or model calls."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def normalize(data, out):
    frame = pd.read_csv(data / "data.csv", dtype={"player_id": "string"})
    required = ["player_id", "team", "position", "games_played", "points_per_game", "minutes_per_game"]
    if not set(required) <= set(frame):
        raise ValueError("Missing required sports columns")
    frame = frame[required].copy()
    frame.insert(0, "source_row", np.arange(1, len(frame) + 1))
    for col in ["player_id", "team", "position"]:
        frame[col] = frame[col].astype("string").str.strip().replace("", pd.NA)
    frame[["team", "position"]] = frame[["team", "position"]].fillna("Unknown")
    for col in ["games_played", "points_per_game", "minutes_per_game"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame.to_csv(out / "normalized.csv", index=False)


def validate(data, out):
    frame = pd.read_csv(out / "normalized.csv", dtype={"player_id": "string"})
    missing = frame.player_id.isna()
    duplicate = frame.player_id.duplicated(keep="first") & ~missing
    games = frame.games_played
    invalid_games = ~(np.isfinite(games) & games.between(0, 82) & (games % 1 == 0))
    reasons = np.select([missing, duplicate, invalid_games], ["missing_player_id", "duplicate_player_id", "invalid_games_played"], default="")
    rejected = frame.loc[reasons != ""].copy()
    rejected["reason"] = reasons[reasons != ""]
    eligible = frame.loc[reasons == ""].copy()
    for col, upper in [("points_per_game", np.inf), ("minutes_per_game", 48)]:
        eligible.loc[~(np.isfinite(eligible[col]) & eligible[col].between(0, upper)), col] = np.nan
    eligible.to_csv(out / "eligible.csv", index=False)
    rejected.to_csv(out / "rejected.csv", index=False)
    write_json(out / "validation.json", {
        "input_rows": len(frame), "eligible_rows": len(eligible), "rejected_rows": len(rejected),
        "rejection_counts": {str(k): int(v) for k, v in rejected.reason.value_counts().items()},
    })


def recover(data, out):
    frame = pd.read_csv(out / "eligible.csv", dtype={"player_id": "string"})
    imputed = {}
    for col in ["points_per_game", "minutes_per_game"]:
        imputed[col] = int(frame[col].isna().sum())
        medians = frame.groupby("position")[col].transform("median")
        valid = frame[col].dropna()
        fallback = float(valid.median()) if len(valid) else 0.0
        frame[col] = frame[col].fillna(medians).fillna(fallback)
    frame["total_points"] = frame.games_played * frame.points_per_game
    frame.sort_values("player_id").to_csv(out / "recovered.csv", index=False)
    quality = json.loads((out / "validation.json").read_text())
    quality["imputed_cells"] = imputed
    write_json(out / "recovery.json", quality)


def report(data, out):
    frame = pd.read_csv(out / "recovered.csv")
    result = json.loads((out / "recovery.json").read_text())
    result["players"] = len(frame)
    result["total_points"] = float(frame.total_points.sum())
    result["players_per_team"] = {str(k): int(v) for k, v in frame.groupby("team").size().items()}
    write_json(out / "quality_report.json", result)


TASKS = {"normalize": normalize, "validate": validate, "recover": recover, "report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--task", choices=list(TASKS))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for task in ([args.task] if args.task else TASKS):
        TASKS[task](args.data_dir, args.output_dir)
