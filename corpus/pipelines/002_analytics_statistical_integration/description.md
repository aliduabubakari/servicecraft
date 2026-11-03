# Linear treatment-score change analysis

Build the sole `linear` batch-05 pipeline with five tasks: validate subjects, derive changes, summarize groups, calculate treatment contrasts, and report. Require unique nonblank subject_id, finite values, scores in [0,100], and binary outcome. Emit subjects_clean.csv sorted by subject_id.

Derive score_change=post_score-baseline_score and improved=1 only when change>0. Group by group into subject_count, baseline/post/change means, sample standard deviation of change (ddof=1), improvement_rate, and outcome_rate. Control must exist. For every non-Control group, use group_summary.csv sufficient statistics to calculate difference_in_mean_change relative to Control, Welch standard error sqrt(var_t/n_t+var_c/n_c), and normal-approximation 95% bounds difference ±1.96*SE. The contrast task also emits contrast_context.json with weighted global measures. experiment_report.json publishes exactly that carried context, avoiding any dependency on earlier stages.

Execution contract: generate executable local Dagster code without networks, prior-run outputs, fixed answers, or human intervention. Preserve the declared topology and artifact-backed dependencies; an alternative node decomposition is acceptable only when logical tasks, observable checkpoints, and dependency semantics remain equivalent. Write outputs below the run output directory. Numeric comparisons use atol=1e-6 and rtol=1e-6; JSON must be finite. Missing columns, invalid identifiers, broken bounds, and non-finite required values fail clearly.

Mandatory output files:
- `subjects_clean.csv`
- `subject_changes.csv`
- `group_summary.csv`
- `treatment_contrasts.csv`
- `contrast_context.json`
- `experiment_report.json`
