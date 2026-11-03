"""Spatial ETL pilot reference, with explicit spherical-distance semantics."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def validate(data, out):
    frame = pd.read_csv(data / "data.csv", dtype={"trip_id": "string", "route": "string"})
    columns = ["trip_id", "route", "origin_lat", "origin_lon", "dest_lat", "dest_lon", "distance_km", "passengers", "delay_minutes"]
    if not set(columns) <= set(frame):
        raise ValueError("Missing required transportation columns")
    frame = frame[columns].copy()
    for col in ["trip_id", "route"]:
        frame[col] = frame[col].str.strip().replace("", pd.NA)
    numeric = columns[2:]
    for col in numeric:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    valid = frame.trip_id.notna() & frame.route.notna() & ~frame.trip_id.duplicated(keep="first")
    valid &= np.isfinite(frame[numeric]).all(axis=1)
    for col in ["origin_lat", "dest_lat"]:
        valid &= frame[col].between(-90, 90)
    for col in ["origin_lon", "dest_lon"]:
        valid &= frame[col].between(-180, 180)
    for col in ["distance_km", "passengers", "delay_minutes"]:
        valid &= frame[col] >= 0
    valid &= frame.passengers % 1 == 0
    frame.loc[valid].to_csv(out / "valid_trips.csv", index=False)
    frame.loc[~valid].to_csv(out / "rejected_trips.csv", index=False)
    write_json(out / "validation.json", {"input_rows": len(frame), "valid_rows": int(valid.sum()), "rejected_rows": int((~valid).sum())})


def spatial(data, out):
    frame = pd.read_csv(out / "valid_trips.csv")
    lat1, lon1, lat2, lon2 = (np.radians(frame[col]) for col in ["origin_lat", "origin_lon", "dest_lat", "dest_lon"])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    frame["great_circle_km"] = 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    frame["passenger_km"] = frame.distance_km * frame.passengers
    frame["detour_ratio"] = frame.distance_km / frame.great_circle_km.where(frame.great_circle_km != 0)
    frame.sort_values("trip_id").to_csv(out / "trip_metrics.csv", index=False)
    write_json(out / "spatial_metadata.json", {"quality": json.loads((out / "validation.json").read_text()), "earth_radius_km": 6371.0088})


def aggregate(data, out):
    frame = pd.read_csv(out / "trip_metrics.csv")
    grouped = frame.groupby("route", sort=True).agg(
        trip_count=("trip_id", "size"), mean_great_circle_km=("great_circle_km", "mean"),
        total_passenger_km=("passenger_km", "sum"), mean_delay_minutes=("delay_minutes", "mean"),
    ).reset_index()
    grouped.to_csv(out / "route_summary.csv", index=False)
    result = json.loads((out / "spatial_metadata.json").read_text())
    result.update({"route_count": len(grouped), "total_passenger_km": float(frame.passenger_km.sum()),
                   "mean_great_circle_km": float(frame.great_circle_km.mean()) if len(frame) else None,
                   "top_routes": grouped.sort_values(["trip_count", "route"], ascending=[False, True]).head(5).route.tolist()})
    write_json(out / "aggregate.json", result)


def report(data, out):
    result = json.loads((out / "aggregate.json").read_text())
    write_json(out / "spatial_report.json", result)


TASKS = {"validate": validate, "spatial": spatial, "aggregate": aggregate, "report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--task", choices=list(TASKS))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for task in ([args.task] if args.task else TASKS):
        TASKS[task](args.data_dir, args.output_dir)
