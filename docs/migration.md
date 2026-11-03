# Standalone repository migration

Created on 3 November 2026 by copying, not moving, the existing benchmark-v1
and standalone Dagster evaluator into `corpus/` and `evaluation/`.
The original project directories were preserved. The new repository has its own
Git history and remote, with no nested Git repositories or application dependency.

Included: all 100 source cases/prompts/fixtures/references, preparation and
qualification tools, runtime controls, expected artifacts, independent oracle
contexts, profiles, schemas, tests and historical qualification summaries.
Excluded from Git: Python environments/caches, editable-install metadata, raw
qualification directories and per-case historical run evidence. Existing local
per-case evidence copies may remain available but are ignored. Historical reports
can name old workspaces; they are evidence records, not active path configuration.

Changes for the combined layout: command paths in guides now point to `corpus/`
and `evaluation/`; fixtures and oracle contexts are tracked for fresh clones;
the oracle Dockerfile accepts a base-image build argument instead of treating a
local image ID as a registry digest; the optional `corpus` installation extra
provides JSON Schema validation. Original behavioral source and input contents
were retained. Source descriptions/prompts still require author semantic review.

Runtime packaging checks also ensure the independent oracle context includes the
new prompt renderer imported by the exporter. The intentional-hang regression
fixture has a 60-second allowance so static analysis can complete before runtime
timeout is tested; its old 10-second allowance could expire during static analysis.

The root README is the current usage entry point. Commands in evaluation-specific
guides run from `evaluation/` unless explicitly described as root commands.
Requalification must produce new evidence for new runtime images; import of an
old successful catalog does not confer approval on a changed environment.
