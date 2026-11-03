"""Qualify batch-05 behavior, topology, failures, and exports."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=["002_analytics_statistical_integration","019_sports_prediction_cleaning_integration","023_sports_regression_clustering_visualization","063_transportation_clustering_validation","079_transportation_regression"]
def load(p):
    def reject(v):raise ValueError(v)
    return json.loads(p.read_text(),parse_constant=reject)
def run(case,data,out,fail=False):
    out.mkdir();r=subprocess.run([sys.executable,str(ROOT/"pipelines"/case/"reference.py"),"--data-dir",str(data),"--output-dir",str(out)],capture_output=True,text=True)
    if fail:assert r.returncode!=0,f"{case} accepted invalid input";return
    if r.returncode:raise RuntimeError(r.stderr)
    for x in load(ROOT/"pipelines"/case/"task_graph.json")["artifacts"]:
        p=out/x["path"];assert p.is_file(),p
        if p.suffix==".csv":assert set(x["required_columns"])<=set(pd.read_csv(p,nrows=0).columns)
        elif p.suffix==".json":load(p)
def check_experiment(data,out):
    src=pd.read_csv(data/"data.csv");changes=pd.read_csv(out/"subject_changes.csv");summary=pd.read_csv(out/"group_summary.csv");contrasts=pd.read_csv(out/"treatment_contrasts.csv")
    np.testing.assert_allclose(changes.score_change,changes.post_score-changes.baseline_score);assert summary.subject_count.sum()==len(src);assert len(contrasts)==len(summary)-1;assert load(out/"contrast_context.json")==load(out/"experiment_report.json")
    assert validate(load(ROOT/"pipelines"/CASES[0]/"task_graph.json"),ROOT/"pipelines"/CASES[0])["structure"]=={"components":1,"roots":1,"sinks":1,"joins":0,"splits":0}
def check_fanout(data,out):
    src=pd.read_csv(data/"data.csv");clean=pd.read_csv(out/"players_clean.csv");team=pd.read_csv(out/"team_availability.csv");position=pd.read_csv(out/"position_compensation.csv");pred=pd.read_csv(out/"all_star_predictions.csv")
    np.testing.assert_allclose(clean.availability_rate,(clean.games_played-clean.injury_games_missed).clip(lower=0)/clean.games_played);assert team.player_count.sum()==position.player_count.sum()==len(src);assert len(pred)==137 and pred.probability.between(0,1).all()
def check_parallel(data,out):
    src=pd.read_csv(data/"data.csv");pred=pd.read_csv(out/"market_value_predictions.csv");clusters=pd.read_csv(out/"player_clusters.csv");profiles=pd.read_csv(out/"cluster_profiles.csv")
    assert len(pred)==115;assert len(clusters)==len(src) and profiles.player_count.sum()==len(src) and set(clusters.cluster)=={0,1,2,3};assert validate(load(ROOT/"pipelines"/CASES[2]/"task_graph.json"),ROOT/"pipelines"/CASES[2])["structure"]=={"components":2,"roots":2,"sinks":2,"joins":0,"splits":0}
def check_cluster(data,out):
    src=pd.read_csv(data/"data.csv");assigned=pd.read_csv(out/"trip_clusters.csv");profiles=pd.read_csv(out/"cluster_profiles.csv");mix=pd.read_csv(out/"route_cluster_mix.csv");report=load(out/"cluster_validation.json")
    assert len(assigned)==len(src) and profiles.trip_count.sum()==len(src) and set(assigned.cluster)=={0,1,2,3,4};np.testing.assert_allclose(mix.groupby("route").route_share.sum(),1);assert sum(report["cluster_sizes"].values())==len(src)
def check_economics(data,out):
    src=pd.read_csv(data/"data.csv");table=pd.read_csv(out/"trip_economics.csv");routes=pd.read_csv(out/"route_profitability.csv");pred=pd.read_csv(out/"profit_predictions.csv");report=load(out/"economics_report.json")
    np.testing.assert_allclose(table.profit,table.revenue-table.operational_cost);np.testing.assert_allclose(table.profit_margin,table.profit/table.revenue);assert routes.trip_count.sum()==len(src) and len(pred)==154;np.testing.assert_allclose(report["total_profit"],src.revenue.sum()-src.operational_cost.sum())
CHECK={CASES[0]:check_experiment,CASES[1]:check_fanout,CASES[2]:check_parallel,CASES[3]:check_cluster,CASES[4]:check_economics}
def corrupt(case,source,dest):
    shutil.copytree(source,dest);p=dest/"data.csv";d=pd.read_csv(p)
    idcol={CASES[0]:"subject_id",CASES[1]:"player_id",CASES[2]:"player_id",CASES[3]:"trip_id",CASES[4]:"trip_id"}[case];d.loc[1,idcol]=d.loc[0,idcol];d.to_csv(p,index=False)
def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix="inlumen-batch05-") as td:
        temp=Path(td)
        for case in CASES:
            source=ROOT/"pipelines"/case;v=validate(load(source/"task_graph.json"),source);out=temp/(case+"-out");run(case,source/"inputs",out);CHECK[case](source/"inputs",out);checks.append({"case":case,"probe":"reference_outputs_independent_invariants_and_topology","status":"passed","topology":v["topology"],"tasks":v["tasks"],"structure":v["structure"],"output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}})
            invalid=temp/(case+"-invalid");corrupt(case,source/"inputs",invalid);run(case,invalid,temp/(case+"-invalid-out"),True);checks.append({"case":case,"probe":"invalid_identifier_rejected","status":"passed"})
            for track in ["natural_language","fixed_graph"]:
                dst=export(case,temp/f"{case}-{track}",track);files={str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file()};assert not any(Path(f).name in {"reference.py","task_graph.json","provenance.json","requirements.txt"} for f in files);assert ("provided_graph.json" in files)==(track=="fixed_graph")
        for case in CASES:
            graph=load(ROOT/"pipelines"/case/"task_graph.json");wrong=copy.deepcopy(graph);wrong["topology"]="linear" if graph["topology"]!="linear" else "fan_out"
            try:validate(wrong)
            except AssertionError:pass
            else:raise AssertionError(f"wrong topology accepted {case}")
        checks.extend([{"case":"batch-05","probe":"incorrect_topology_labels_rejected","status":"passed"},{"case":"batch-05","probe":"generator_input_allowlist_both_tracks","status":"passed"}])
    report={"status":"passed","scope":"Batch-05 Python references, independent invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation","dagster_runtime_qualification":"not_run","review_status":"author_review_pending","python":sys.version.split()[0],"packages":{n:version(n) for n in ["pandas","numpy","scikit-learn","jsonschema"]},"checks":checks};(ROOT/"qualification-report-batch05.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({"status":"passed","check_groups":len(checks),"dagster_runtime_qualification":"not_run"},indent=2))
if __name__=="__main__":main()
