"""Known-good recovery control for visible fixture; not a scored LLM generation."""

import os
from pathlib import Path
import dagster as dg
import numpy as np
import pandas as pd

OUT = Path(os.environ["SERVICECRAFT_OUTPUT_DIR"])
NUMS = [
    "games_played",
    "points_per_game",
    "assists_per_game",
    "rebounds_per_game",
    "minutes_per_game",
    "age",
    "experience_years",
    "salary_millions",
]


def save(frame, filename):
    frame.to_csv(OUT / filename, index=False)
    return frame


@dg.asset
def audit():
    frame = pd.read_csv(Path(os.environ["SERVICECRAFT_INPUT_DIR"]) / "data.csv")
    if frame.player_id.isna().any() or not frame.player_id.is_unique:
        raise ValueError("invalid player identifiers")
    frame[["team", "position"]] = frame[["team", "position"]].replace(r"^\s*$", np.nan, regex=True)
    for c in NUMS:
        frame[c] = pd.to_numeric(frame[c], errors="coerce")
    for name, col in [
        ("points", "points_per_game"),
        ("salary", "salary_millions"),
        ("team", "team"),
        ("position", "position"),
    ]:
        frame[f"missing_{name}_input"] = frame[col].isna().astype(int)
    return save(frame.sort_values("player_id"), "audited_players.csv")


@dg.asset
def numeric(audit):
    frame = audit.copy()
    for col in NUMS:
        frame[col] = frame[col].fillna(frame.groupby("position")[col].transform("median"))
        frame[col] = frame[col].fillna(frame[col].median())
    if not np.isfinite(frame[NUMS].to_numpy(float)).all():
        raise ValueError("unrecoverable numeric values")
    return save(frame, "numeric_recovered.csv")


@dg.asset
def categorical(numeric):
    frame = numeric.copy()
    for col in ["team", "position"]:
        counts = frame[col].dropna().value_counts()
        mode = sorted(counts[counts == counts.max()].index.astype(str))[0]
        frame[col] = frame[col].fillna(mode)
    frame["age_band"] = pd.cut(
        frame.age, [0, 24, 29, 34, np.inf], labels=["<=24", "25-29", "30-34", "35+"]
    ).astype(str)
    return save(frame, "players_recovered.csv")


def cohort(frame, group, filename):
    summary = (
        frame.groupby(group, as_index=False)
        .agg(
            player_count=("player_id", "size"),
            mean_points=("points_per_game", "mean"),
            mean_salary=("salary_millions", "mean"),
            recovered_points=("missing_points_input", "sum"),
            recovered_salary=("missing_salary_input", "sum"),
            recovered_team=("missing_team_input", "sum"),
            recovered_position=("missing_position_input", "sum"),
        )
        .sort_values(group)
    )
    return save(summary, filename)


@dg.asset
def teams(categorical):
    return cohort(categorical, "team", "team_summary.csv")


@dg.asset
def positions(categorical):
    return cohort(categorical, "position", "position_summary.csv")


@dg.asset
def ages(categorical):
    return cohort(categorical, "age_band", "age_summary.csv")


defs = dg.Definitions(assets=[audit, numeric, categorical, teams, positions, ages])
