# Independent sports summaries converging into one report

Build a pure fan-in graph. Three independent root tasks compute team production, position play/shooting, and four age-band summaries directly from the input. A final task consumes all three summaries, reconciles their player totals, and reports summary counts and the highest-scoring team. The branches must not depend on one another.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Invalid identifiers, missing columns, or non-finite required values must fail clearly.

Mandatory output files:
- `team_summary.csv`
- `position_summary.csv`
- `age_summary.csv`
- `sports_report.json`
