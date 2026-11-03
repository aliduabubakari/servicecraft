"""A small neutral Dagster submission: two independent sources converge."""

import json
import os
from pathlib import Path

import dagster as dg


def emit(name, value):
    (Path(os.environ["SERVICECRAFT_OUTPUT_DIR"]) / name).write_text(json.dumps({"value": value}))
    return value


@dg.asset
def left():
    data = json.loads((Path("/inputs") / "data.json").read_text())
    return emit("left.json", sum(data["left"]))


@dg.asset
def right():
    data = json.loads((Path("/inputs") / "data.json").read_text())
    return emit("right.json", sum(data["right"]))


@dg.asset
def total(left, right):
    return emit("total.json", left + right)


defs = dg.Definitions(assets=[left, right, total])
