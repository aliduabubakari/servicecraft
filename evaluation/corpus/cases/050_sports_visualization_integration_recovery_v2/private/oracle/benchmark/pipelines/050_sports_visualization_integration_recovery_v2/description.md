# Recovered players fanning out to cohort summaries

Build a six-task linear-to-fan-out graph over the supplied defect-bearing fixture. Audit and append four missing-input flags; recover numeric fields with position median then global median; recover team and position with deterministic global modes and derive fixed age bands. Fan the recovered artifact into independent team, position, and age summaries carrying recovery counts. Duplicate or blank IDs fail. The documented defects are one points value, one salary, one team, and one position.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for explicitly documented recovery fixtures, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `audited_players.csv`
- `numeric_recovered.csv`
- `players_recovered.csv`
- `team_summary.csv`
- `position_summary.csv`
- `age_summary.csv`
