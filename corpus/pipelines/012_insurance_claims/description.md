# Independent claims analyses converging into a portfolio report

Build a pure `fan_in` claims DAG. Three independent root tasks read claims.csv and each validates unique nonblank claim_id, parseable incident/report dates, nonnegative finite claim amount/delay, and binary is_fraudulent. The synthetic source's report_delay_days is an authoritative supplied duration and is not derived from or checked against the independently generated calendar dates. There is intentionally no shared preparation artifact: each branch owns the checks relevant to its result. Their outputs converge only at the final report task.

Financial branch groups by claim_type into claim_count, total/mean/median claim amount. Processing branch groups by claim_status into claim_count, mean/median report delay, and mean claim amount. Fraud branch groups by policy_type into claim_count, fraud_count, fraud_rate, and mean claim amount. Sort each output by group key.

claims_report.json consumes all three branch artifacts and contains claims, total_claim_amount, fraudulent_claims, highest_amount_claim_type, slowest_claim_status, and highest_fraud_rate_policy_type. Rankings are descending on the named measure with group name ascending as tie-breaker. The join is a reporting dependency, not permission for the three analysis branches to depend on each other.

Execution contract: generate executable local Dagster code without network services, prior-run outputs, fixed analytical answers, or human intervention. The declared topology is a scored semantic property: preserve independent branches and every artifact-backed join. Alternative Dagster decomposition is allowed only when logical requirements, dependencies, topology, and observable checkpoints remain equivalent. Write outputs beneath the run output directory. Preserve numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid identifiers/dates, broken relationships, and non-finite required values must fail clearly.

Mandatory output files:
- `financial_by_claim_type.csv`
- `processing_by_status.csv`
- `fraud_by_policy_type.csv`
- `claims_report.json`
