# Three player feature branches feeding four cohort analyses

Build a ten-task fan-in/fan-out graph. Validate players; independently derive performance, shooting, and context features with fixed age and salary bands; join all three one-to-one. Fan the integrated table into team, position, age-band, and salary-band summaries, then reconverge all four artifacts into a report that reconciles player totals and group counts. Performance includes production and safe per-minute production; shooting includes mean and weighted indices.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `players_clean.csv`
- `performance_features.csv`
- `shooting_features.csv`
- `context_features.csv`
- `analysis_table.csv`
- `team_summary.csv`
- `position_summary.csv`
- `age_summary.csv`
- `salary_summary.csv`
- `sports_report.json`
