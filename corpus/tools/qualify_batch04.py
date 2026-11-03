"""Qualify batch-04 behavior, topology, failure handling, and exports."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=["011_hr_visualization_integration_validation","012_insurance_claims","013_predictive_maintenance","015_sports_clustering_prediction_statistical","055_transportation_analysis"]
def load(path):
    def reject(v):raise ValueError("non-finite JSON "+v)
    return json.loads(path.read_text(),parse_constant=reject)
def run(case,data,out,fail=False):
    out.mkdir();r=subprocess.run([sys.executable,str(ROOT/"pipelines"/case/"reference.py"),"--data-dir",str(data),"--output-dir",str(out)],capture_output=True,text=True)
    if fail:assert r.returncode!=0,f"{case} accepted invalid data";return
    if r.returncode:raise RuntimeError(r.stderr)
    for item in load(ROOT/"pipelines"/case/"task_graph.json")["artifacts"]:
        p=out/item["path"];assert p.is_file(),p
        if p.suffix==".csv":assert set(item["required_columns"])<=set(pd.read_csv(p,nrows=0).columns)
        elif p.suffix==".json":load(p)
def check_hr(data,out):
    src=pd.read_csv(data/"hr_data.csv");clean=pd.read_csv(out/"workforce_clean.csv");comp=pd.read_csv(out/"compensation_by_department.csv");perf=pd.read_csv(out/"performance_by_department.csv");composition=pd.read_csv(out/"workforce_composition.csv")
    np.testing.assert_allclose(clean.total_compensation,clean.salary+clean.bonus);assert comp.employee_count.sum()==perf.employee_count.sum()==composition.employee_count.sum()==len(src);np.testing.assert_allclose(comp.total_bonus.sum(),src.bonus.sum())
    assert validate(load(ROOT/"pipelines"/CASES[0]/"task_graph.json"),ROOT/"pipelines"/CASES[0])["structure"]=={"components":1,"roots":1,"sinks":3,"joins":0,"splits":1}
def check_claims(data,out):
    src=pd.read_csv(data/"claims.csv");fin=pd.read_csv(out/"financial_by_claim_type.csv");proc=pd.read_csv(out/"processing_by_status.csv");fraud=pd.read_csv(out/"fraud_by_policy_type.csv");report=load(out/"claims_report.json")
    assert fin.claim_count.sum()==proc.claim_count.sum()==fraud.claim_count.sum()==len(src);np.testing.assert_allclose(fin.total_claim_amount.sum(),src.claim_amount.sum());assert fraud.fraud_count.sum()==src.is_fraudulent.sum();assert report["claims"]==len(src) and report["fraudulent_claims"]==int(src.is_fraudulent.sum())
def check_maintenance(data,out):
    src=pd.read_csv(data/"sensor_readings.csv");features=pd.read_csv(out/"maintenance_features.csv");risk=pd.read_csv(out/"machine_risk_summary.csv");p24=pd.read_csv(out/"failure24h_predictions.csv");p7=pd.read_csv(out/"failure7d_predictions.csv")
    assert len(features)==len(src)-24*src.machine_id.nunique()==21360;assert risk.observations.sum()==len(features);assert len(p24)==len(p7)==len(features)-math_floor(.8*len(features));assert p24.probability.between(0,1).all() and p7.probability.between(0,1).all()
    report=load(out/"maintenance_report.json");assert report["rows"]==len(features) and report["machines"]==10
def math_floor(value):return int(np.floor(value))
def check_sports(data,out):
    src=pd.read_csv(data/"data.csv");clusters=pd.read_csv(out/"player_clusters.csv");profiles=pd.read_csv(out/"cluster_profiles.csv");pred=pd.read_csv(out/"all_star_predictions.csv")
    assert len(clusters)==len(src) and set(clusters.cluster)=={0,1,2,3} and profiles.player_count.sum()==len(src);assert len(pred)==130 and pred.probability.between(0,1).all()
    assert validate(load(ROOT/"pipelines"/CASES[3]/"task_graph.json"),ROOT/"pipelines"/CASES[3])["structure"]=={"components":2,"roots":2,"sinks":2,"joins":0,"splits":0}
def check_transport(data,out):
    src=pd.read_csv(data/"data.csv");features=pd.read_csv(out/"trip_features.csv");train=pd.read_csv(out/"train.csv");test=pd.read_csv(out/"test.csv");pred=pd.read_csv(out/"predictions.csv")
    expected=np.where(features.passengers>0,features.fare_amount/features.passengers,0);np.testing.assert_allclose(features.fare_per_passenger,expected);assert len(train)==478 and len(test)==len(pred)==120;assert set(train.trip_id)|set(test.trip_id)==set(src.trip_id);assert load(out/"metrics.json")==load(out/"delay_report.json")
CHECK={CASES[0]:check_hr,CASES[1]:check_claims,CASES[2]:check_maintenance,CASES[3]:check_sports,CASES[4]:check_transport}
def corrupt(case,source,dest):
    shutil.copytree(source,dest)
    if case==CASES[0]:p=dest/"hr_data.csv";d=pd.read_csv(p);d.loc[1,"emp_id"]=d.loc[0,"emp_id"]
    elif case==CASES[1]:p=dest/"claims.csv";d=pd.read_csv(p);d.loc[1,"claim_id"]=d.loc[0,"claim_id"]
    elif case==CASES[2]:p=dest/"sensor_readings.csv";d=pd.read_csv(p);d.loc[1,"timestamp"]=d.loc[0,"timestamp"]
    elif case==CASES[3]:p=dest/"data.csv";d=pd.read_csv(p);d.loc[1,"player_id"]=d.loc[0,"player_id"]
    else:p=dest/"data.csv";d=pd.read_csv(p);d.loc[0,"departure_hour"]=24
    d.to_csv(p,index=False)
def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix="inlumen-batch04-") as td:
        temp=Path(td)
        for case in CASES:
            source=ROOT/"pipelines"/case;v=validate(load(source/"task_graph.json"),source);out=temp/(case+"-out");run(case,source/"inputs",out);CHECK[case](source/"inputs",out)
            checks.append({"case":case,"probe":"reference_outputs_independent_invariants_and_topology","status":"passed","topology":v["topology"],"tasks":v["tasks"],"structure":v["structure"],"output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}})
            invalid=temp/(case+"-invalid");corrupt(case,source/"inputs",invalid);run(case,invalid,temp/(case+"-invalid-out"),True);checks.append({"case":case,"probe":"invalid_input_contract_rejected","status":"passed"})
            for track in ["natural_language","fixed_graph"]:
                dst=export(case,temp/f"{case}-{track}",track);files={str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file()};assert not any(Path(f).name in {"reference.py","task_graph.json","provenance.json","requirements.txt"} for f in files);assert ("provided_graph.json" in files)==(track=="fixed_graph")
        for case in CASES:
            graph=load(ROOT/"pipelines"/case/"task_graph.json");wrong=copy.deepcopy(graph);wrong["topology"]="linear" if graph["topology"]!="linear" else "fan_in"
            try:validate(wrong)
            except AssertionError:pass
            else:raise AssertionError(f"wrong topology accepted: {case}")
        checks.extend([{"case":"batch-04","probe":"incorrect_topology_labels_rejected","status":"passed"},{"case":"batch-04","probe":"generator_input_allowlist_both_tracks","status":"passed"}])
    report={"status":"passed","scope":"Batch-04 Python references, independent invariants, invalid-input rejection, topology classification, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation","dagster_runtime_qualification":"not_run","review_status":"author_review_pending","python":sys.version.split()[0],"packages":{n:version(n) for n in ["pandas","numpy","scikit-learn","jsonschema"]},"checks":checks};(ROOT/"qualification-report-batch04.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({"status":"passed","check_groups":len(checks),"dagster_runtime_qualification":"not_run"},indent=2))
if __name__=="__main__":main()
