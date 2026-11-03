"""Generate a corpus-level task/topology inventory from batch manifests and graphs."""
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    batches=[];all_cases=[]
    for manifest_path in sorted(ROOT.glob("batch-*.json")):
        manifest=json.loads(manifest_path.read_text());batch_id=manifest.get("batch_id",manifest_path.stem);cases=[]
        for item in manifest.get("cases",[]):
            graph=json.loads((ROOT/"pipelines"/item["pipeline_id"]/"task_graph.json").read_text())
            case={"pipeline_id":graph["pipeline_id"],"domain":graph["domain"],"family_id":graph["family_id"],"topology":graph["topology"],"tasks":len(graph["tasks"]),"dependencies":len(graph["dependencies"])}
            cases.append(case);all_cases.append(case)
        topology_counts=Counter(case["topology"] for case in cases);task_counts=[case["tasks"] for case in cases]
        batches.append({"batch_id":batch_id,"case_count":len(cases),"linear_cases":topology_counts["linear"],"distinct_topologies":len(topology_counts),"topology_counts":dict(sorted(topology_counts.items())),"task_count_range":[min(task_counts),max(task_counts)] if task_counts else [],"complies_with_new_batch_policy":topology_counts["linear"]<=1 and len(topology_counts)>=min(4,len(cases)),"cases":cases})
    topology_counts=Counter(case["topology"] for case in all_cases);task_counts=[case["tasks"] for case in all_cases]
    result={"policy":{"maximum_linear_cases_per_new_five_case_batch":1,"minimum_distinct_topologies_per_new_five_case_batch":4,"topology_must_be_computation_justified":True,"task_count_must_follow_required_observable_operations":True},"corpus":{"case_count":len(all_cases),"topology_counts":dict(sorted(topology_counts.items())),"task_count_range":[min(task_counts),max(task_counts)],"distinct_domains":len({case['domain'] for case in all_cases}),"distinct_families":len({case['family_id'] for case in all_cases})},"batches":batches,"migration_note":"Batches 01 and 02 predate the topology-diversity policy and remain queued for behavioral/topology redesign; relabeling without real dependency changes is prohibited."}
    (ROOT/"corpus-diversity.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result["corpus"],indent=2))


if __name__=="__main__":main()
