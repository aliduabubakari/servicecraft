# Standardized task prompts

Each of the 100 cases has a UTF-8 task description at
`corpus/cases/<case-id>/prompt.txt`. It is byte-identical to the source benchmark's
rendered `prompt.txt`. Template `servicecraft.task-prompt@2` uses seven consistent
sections: objective, available inputs, processing, dependencies/topology, outputs,
execution/numerical rules and deliverable. It preserves every task-specific
description paragraph and output annotation, adds input filenames/CSV headers,
and provides common topology-preservation and delivery instructions. It does not
read reference graphs, control implementations or private evaluation answers.
Author semantic review remains pending; formatting is not semantic certification.

`corpus/prompt-manifest.json` records template/renderer identity and per-case
description, input-inventory and prompt SHA-256 values. This prompt revision
does not modify the executable controls, private oracles or their prior runtime
qualification. Qualification does not imply the new prompts were tested through
an LLM generation experiment.

Use the same task text for direct generation, InLumen, Pi and Aider. Supply a
separate frozen common runtime/submission contract and the allowed inputs. A
`prompt.txt` alone does not define all driver/runtime packaging instructions.
Record hashes for both the task text and the common instructions. Do not send
both `description.md` and `prompt.txt` into the model context.

Do not mount a complete evaluation case directory into a coding agent: it also
contains trusted controls, private answers and qualification evidence. Use the
benchmark allowlist exporter to create a fresh generation workspace:

```sh
python3 corpus/tools/export_inputs.py \
  001_analytics_statistical_cleaning_integration /tmp/case001-natural \
  --track natural_language
```

Run this command from the ServiceCraft repository root. Natural-language
exports include the prompt, source description and inputs. Fixed-graph exports
add a sanitized `provided_graph.json` intentionally. The natural-language prompt
does not obtain that graph. The exporter refuses an existing destination.

After editing source descriptions, synchronize with
`corpus/tools/sync_prompts.py --evaluation-corpus
evaluation/corpus`, then run the same command with `--check`.
Future source/corpus rebuilds must rerun this publication step. Modifying task
requirements also requires reviewing and requalifying the affected controls and
oracles before freezing an experiment.
