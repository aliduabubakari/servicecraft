"""Known-good smoke control, authored for evaluator qualification, not an LLM result."""

import json
import os
from pathlib import Path
import dagster as dg
import numpy as np
import pandas as pd

OUT = Path(os.environ["SERVICECRAFT_OUTPUT_DIR"])


def save(frame, filename):
    frame.to_csv(OUT / filename, index=False)
    return frame


@dg.asset
def prepare():
    data = pd.read_csv(Path(os.environ["SERVICECRAFT_INPUT_DIR"]) / "data.csv")
    if data.trip_id.isna().any() or not data.trip_id.is_unique:
        raise ValueError("invalid trip identifiers")
    data = data.sort_values("trip_id").copy()
    data["passenger_km"] = data.distance_km * data.passengers
    data["on_time"] = (data.delay_minutes <= 5).astype(int)
    return save(data, "trips_prepared.csv")


@dg.asset
def summarize(prepare):
    frame = (
        prepare.groupby("route", as_index=False)
        .agg(
            trip_count=("trip_id", "size"),
            total_passenger_km=("passenger_km", "sum"),
            mean_passengers=("passengers", "mean"),
            mean_fare=("fare_amount", "mean"),
            mean_delay=("delay_minutes", "mean"),
            on_time_rate=("on_time", "mean"),
        )
        .sort_values("route")
    )
    return save(frame, "route_summary.csv")


@dg.asset
def rank(summarize):
    frame = summarize.sort_values(
        ["total_passenger_km", "on_time_rate", "route"], ascending=[False, False, True]
    ).reset_index(drop=True)
    frame.insert(1, "rank", np.arange(1, len(frame) + 1))
    return save(frame, "route_ranking.csv")


@dg.asset
def chart(rank):
    frame = rank[
        ["route", "rank", "trip_count", "total_passenger_km", "mean_delay", "on_time_rate"]
    ].copy()
    frame["passenger_km_label"] = frame.total_passenger_km.round(2).astype(str)
    return save(frame, "route_chart_data.csv")


@dg.asset
def report(chart):
    payload = dict(
        trips=int(chart.trip_count.sum()),
        routes=len(chart),
        top_route=chart.iloc[0].route,
        top_total_passenger_km=float(chart.iloc[0].total_passenger_km),
    )
    (OUT / "route_report.json").write_text(json.dumps(payload, allow_nan=False))


defs = dg.Definitions(assets=[prepare, summarize, rank, chart, report])
