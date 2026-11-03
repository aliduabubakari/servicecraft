"""Publish standardized public task prompts; never read reference graphs or answers."""

import argparse
import hashlib
import json
from pathlib import Path

from prompt_format import VERSION, render_prompt
ROOT = Path(__file__).resolve().parents[1]


def sync_prompts(root=ROOT, evaluation_corpus=None, check=False):
    sources = sorted((Path(root) / "pipelines").iterdir())
    sources = [p for p in sources if p.is_dir() and (p / "description.md").is_file()]
    if not sources:
        raise ValueError("No pipeline descriptions found")
    targets = []
    records = []
    if evaluation_corpus is not None:
        cases = Path(evaluation_corpus) / "cases"
        actual = {p.name for p in cases.iterdir() if p.is_dir()}
        if actual != {p.name for p in sources}:
            raise ValueError("Evaluation corpus case IDs differ from benchmark descriptions")
    for source in sources:
        content, metadata = render_prompt(source)
        records.append(metadata)
        targets.append((source / "prompt.txt", content))
        if evaluation_corpus is not None:
            targets.append((Path(evaluation_corpus) / "cases" / source.name / "prompt.txt", content))
    manifest = {
        "schema_version": "servicecraft.prompt-manifest@1",
        "template_version": VERSION,
        "renderer_sha256": hashlib.sha256(Path(__file__).with_name("prompt_format.py").read_bytes()).hexdigest(),
        "case_count": len(records),
        "cases": records,
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    prompt_file_count = len(targets)
    targets.append((Path(root) / "prompt-manifest.json", manifest_bytes))
    if evaluation_corpus is not None:
        targets.append((Path(evaluation_corpus) / "prompt-manifest.json", manifest_bytes))
    if check:
        stale = [str(p) for p, content in targets if not p.is_file() or p.read_bytes() != content]
        if stale:
            raise ValueError("Missing or stale prompt files:\n" + "\n".join(stale))
    else:
        for path, content in targets:
            path.write_bytes(content)
    # A deterministic digest of ordered case IDs and exact task-prompt content.
    digest = hashlib.sha256()
    for record in records:
        digest.update(record["case_id"].encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(record["prompt_sha256"]))
    return {"cases": len(sources), "prompt_files": prompt_file_count, "checked": check,
            "template_version": VERSION,
            "collection_sha256": digest.hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-root", type=Path, default=ROOT)
    parser.add_argument("--evaluation-corpus", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(sync_prompts(args.benchmark_root, args.evaluation_corpus, args.check), indent=2))
