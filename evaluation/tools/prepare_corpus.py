"""Create standalone trusted controls for every source case using a pinned runtime."""

import argparse
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="servicecraft-runtime:1.13.12")
    args = parser.parse_args()
    benchmark = args.benchmark_root.resolve()
    project = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o777)
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", args.image]))[0]["Id"]
    cmd = [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--user",
        "65532:65532",
        "--tmpfs",
        "/tmp:rw,size=512m",
    ]
    for source, target in [
        (benchmark, "/benchmark"),
        (project, "/servicecraft"),
        (output, "/prepared"),
    ]:
        cmd += [
            "--mount",
            f"type=bind,source={source},target={target}"
            + ("" if target == "/prepared" else ",readonly"),
        ]
    result = subprocess.run(cmd + [image, "python", "/servicecraft/tools/prepare_corpus_worker.py"])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
