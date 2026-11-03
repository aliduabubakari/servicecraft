# Parallel team-performance and regional home-location analysis

Build two disconnected three-task components. The performance component computes production_index=points+assists+rebounds and safe production-per-minute, aggregates player counts, production, per-minute production and salary by team, then reports the highest-production team. The geographic component independently validates latitude/longitude bounds, aggregates home-location counts, centroids and coordinate spans by region, then reports the largest region. Neither component consumes artifacts from the other.

Execution contract: generate executable local Dagster code without networks, prior outputs, fixed answers, or human intervention. Preserve the declared artifact-backed topology and write beneath the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must contain only finite values. Reject missing required columns, blank or duplicate identifiers, and non-finite required numeric values.

Mandatory output files:
- `player_performance.csv`
- `team_performance.csv`
- `performance_report.json`
- `player_geography.csv`
- `region_summary.csv`
- `geography_report.json`
