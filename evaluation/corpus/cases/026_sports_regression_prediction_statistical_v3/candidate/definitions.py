import json, os
from pathlib import Path
import support
from control_engine import build_definitions
root=Path(__file__).parent
support.__file__=str(root / '026_sports_regression_prediction_statistical_v3' / "reference.py")
defs=build_definitions(json.loads((root/"graph.json").read_text()),json.loads((root/"plan.json").read_text()),vars(support),Path(os.environ["SERVICECRAFT_INPUT_DIR"]),Path(os.environ["SERVICECRAFT_OUTPUT_DIR"]))
