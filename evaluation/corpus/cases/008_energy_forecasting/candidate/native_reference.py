"""Lagged energy regression pilot. Current/future weather is not a feature."""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES = ["lag_24h_kwh", "hour", "day_of_week", "month", "is_holiday", "previous_temp_avg", "previous_humidity_avg", "previous_cloud_cover_avg", "previous_wind_avg"]
WEATHER = ["temp_avg", "humidity_avg", "cloud_cover_avg", "wind_avg"]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def ingest(data, out):
    energy = pd.read_csv(data / "energy_consumption.csv")
    weather = pd.read_csv(data / "weather.csv")
    energy = energy[["timestamp", "consumption_kwh", "is_holiday"]].copy()
    weather = weather[["date", *WEATHER]].copy()
    energy["timestamp"] = pd.to_datetime(energy.timestamp, errors="raise")
    weather["date"] = pd.to_datetime(weather.date, errors="raise")
    energy = energy.sort_values("timestamp")
    weather = weather.sort_values("date")
    if energy.timestamp.duplicated().any() or weather.date.duplicated().any():
        raise ValueError("Duplicate timestamp/date")
    if not (energy.timestamp.diff().dropna() == pd.Timedelta(hours=1)).all():
        raise ValueError("Energy timestamps must be continuous hourly observations")
    for frame, cols in [(energy, ["consumption_kwh", "is_holiday"]), (weather, WEATHER)]:
        for col in cols:
            frame[col] = pd.to_numeric(frame[col], errors="raise")
        if not np.isfinite(frame[cols]).all().all():
            raise ValueError("Non-finite energy/weather value")
    if (energy.consumption_kwh < 0).any() or not energy.is_holiday.isin([0, 1]).all():
        raise ValueError("Invalid target or holiday flag")
    energy.to_csv(out / "hourly.csv", index=False)
    weather.to_csv(out / "daily_weather.csv", index=False)


def align(data, out):
    energy = pd.read_csv(out / "hourly.csv", parse_dates=["timestamp"])
    weather = pd.read_csv(out / "daily_weather.csv", parse_dates=["date"])
    energy["date"] = energy.timestamp.dt.normalize()
    weather["date"] += pd.Timedelta(days=1)
    weather = weather.rename(columns={col: "previous_" + col for col in WEATHER})
    frame = energy.merge(weather, on="date", how="left", validate="many_to_one").sort_values("timestamp")
    frame.to_csv(out / "aligned.csv", index=False)


def features(data, out):
    frame = pd.read_csv(out / "aligned.csv", parse_dates=["timestamp"])
    frame["lag_24h_kwh"] = frame.consumption_kwh.shift(24)
    frame["hour"] = frame.timestamp.dt.hour
    frame["day_of_week"] = frame.timestamp.dt.dayofweek
    frame["month"] = frame.timestamp.dt.month
    frame = frame.dropna(subset=FEATURES)
    if len(frame) < 10:
        raise ValueError("Insufficient eligible observations")
    frame[["timestamp", "consumption_kwh", *FEATURES]].to_csv(out / "features.csv", index=False)


def split(data, out):
    frame = pd.read_csv(out / "features.csv")
    boundary = int(np.floor(0.8 * len(frame)))
    frame.iloc[:boundary].to_csv(out / "train.csv", index=False)
    frame.iloc[boundary:].to_csv(out / "test.csv", index=False)


def fit_predict(data, out):
    train = pd.read_csv(out / "train.csv")
    test = pd.read_csv(out / "test.csv")
    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0, fit_intercept=True, solver="svd"))
    model.fit(train[FEATURES], train.consumption_kwh)
    prediction = model.predict(test[FEATURES])
    pd.DataFrame({"timestamp": test.timestamp, "actual_kwh": test.consumption_kwh, "predicted_kwh": prediction}).to_csv(out / "predictions.csv", index=False)
    with (out / "model.pkl").open("wb") as handle:
        pickle.dump(model, handle)
    write_json(out / "fit_metadata.json", {"train_rows": len(train), "test_rows": len(test), "features": FEATURES, "alpha": 1.0,
        "scaler_mean": model[0].mean_.tolist(), "scaler_scale": model[0].scale_.tolist()})


def evaluate(data, out):
    frame = pd.read_csv(out / "predictions.csv")
    error = frame.actual_kwh - frame.predicted_kwh
    metrics = json.loads((out / "fit_metadata.json").read_text())
    metrics.update({"mae_kwh": float(np.abs(error).mean()), "rmse_kwh": float(np.sqrt((error**2).mean()))})
    write_json(out / "metrics.json", metrics)


def report(data, out):
    write_json(out / "energy_report.json", json.loads((out / "metrics.json").read_text()))


TASKS = {"ingest": ingest, "align": align, "features": features, "split": split, "fit_predict": fit_predict, "evaluate": evaluate, "report": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--task", choices=list(TASKS))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for task in ([args.task] if args.task else TASKS):
        TASKS[task](args.data_dir, args.output_dir)
