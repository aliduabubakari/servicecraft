# Independent sports summaries converging into one report

Build pure fan-in. Three independent roots validate the same player input and emit: team production counts/means; position shooting counts/percentage means; and experience-band (0-3,4-7,8-12,13+) counts with mean salary/minutes. A single final report consumes all three and publishes reconciled player count, teams, positions, bands, and highest-scoring team with team-name tie-break. Branches must not depend on each other.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies. Alternative decomposition is acceptable only when logical tasks, checkpoints, and dependency semantics remain equivalent. Write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Invalid identifiers, missing columns, and non-finite required values fail clearly.

Mandatory output files:
- `team_production.csv`
- `position_shooting.csv`
- `experience_summary.csv`
- `sports_summary_report.json`
