# Linear audited recovery and team summary

Build the sole five-task linear case over the supplied defect-bearing fixture. Audit missing values and append four input-missing flags; recover numeric values with position median followed by global median fallback; recover blank team and position with the deterministic global mode (alphabetically first on ties); aggregate team player counts, mean points/salary/experience, and recovery-flag counts; publish validation and recovery reports. Duplicate or blank player IDs still fail. Exactly four documented input cells are defective: one points value, one salary value, one team, and one position.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Except for the explicitly documented recovery fixture, reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `audited_players.csv`
- `numeric_recovered.csv`
- `players_recovered.csv`
- `team_summary.csv`
- `validation_audit.json`
- `recovery_report.json`
