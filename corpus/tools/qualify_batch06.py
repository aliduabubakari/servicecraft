"""Qualify batch-06 references, topology, failures, and exports."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=["017_sports_clustering_statistical_visualization","020_sports_prediction_statistical_visualization","030_sports_statistical_cleaning","084_transportation_statistical_cleaning_integration","099_transportation_visualization_recovery_reporting"]
def load(p):
 def reject(v):raise ValueError(v)
 return json.loads(p.read_text(),parse_constant=reject)
def run(case,data,out,fail=False):
 out.mkdir();r=subprocess.run([sys.executable,str(ROOT/"pipelines"/case/"reference.py"),"--data-dir",str(data),"--output-dir",str(out)],capture_output=True,text=True)
 if fail:assert r.returncode!=0;return
 if r.returncode:raise RuntimeError(r.stderr)
 for x in load(ROOT/"pipelines"/case/"task_graph.json")["artifacts"]:
  p=out/x["path"];assert p.is_file(),p
  if p.suffix==".csv":assert set(x["required_columns"])<=set(pd.read_csv(p,nrows=0).columns)
  elif p.suffix==".json":load(p)
def c_style(data,out):
 src=pd.read_csv(data/"data.csv");clusters=pd.read_csv(out/"player_clusters.csv");profile=pd.read_csv(out/"cluster_profiles.csv");mix=pd.read_csv(out/"position_cluster_mix.csv");scatter=pd.read_csv(out/"cluster_scatter_data.csv");report=load(out/"style_report.json");assert len(clusters)==len(scatter)==len(src) and profile.player_count.sum()==len(src);np.testing.assert_allclose(mix.groupby("position").position_share.sum(),1);assert report["players"]==len(src) and report["clusters"]==5
def c_parallel(data,out):
 src=pd.read_csv(data/"data.csv");pred=pd.read_csv(out/"all_star_predictions.csv");pos=pd.read_csv(out/"position_statistics.csv");team=pd.read_csv(out/"team_chart_data.csv");assert len(pred)==139 and pos.player_count.sum()==team.player_count.sum()==len(src);assert validate(load(ROOT/"pipelines"/CASES[1]/"task_graph.json"),ROOT/"pipelines"/CASES[1])["structure"]=={"components":3,"roots":3,"sinks":3,"joins":0,"splits":0}
def c_rank(data,out):
 src=pd.read_csv(data/"data.csv");f=pd.read_csv(out/"player_features.csv");ranked=pd.read_csv(out/"ranked_players.csv");top=pd.read_csv(out/"top_players_by_position.csv");np.testing.assert_allclose(f.production_index,f.points_per_game+f.assists_per_game+f.rebounds_per_game);assert ranked.overall_rank.tolist()==list(range(1,len(src)+1));assert len(top)==5*src.position.nunique();assert load(out/"ranking_report.json")["overall_leader"]==ranked.iloc[0].player_id
def c_reliability(data,out):
 src=pd.read_csv(data/"data.csv");score=pd.read_csv(out/"route_scores.csv");ranked=pd.read_csv(out/"ranked_routes.csv");report=load(out/"route_report.json");np.testing.assert_allclose(score.combined_score,(score.mean_on_time_pct+score.mean_satisfaction/5)/2);assert ranked.trip_count.sum()==len(src) and report["top_route"]==ranked.iloc[0].route
def c_recovery(data,out):
 src=pd.read_csv(data/"data.csv");recovered=pd.read_csv(out/"trips_recovered.csv");audit=load(out/"recovery_audit.json");assert len(recovered)==len(src) and recovered[["passengers","fare_amount","delay_minutes"]].notna().all().all();assert audit["imputed_numeric"]=={"passengers":1,"fare_amount":1,"delay_minutes":1} and audit["unknown_vehicle_type"]==audit["unknown_weather_condition"]==1
 for name,key in [("route_summary.csv","route"),("vehicle_summary.csv","vehicle_type"),("weather_summary.csv","weather_condition")]:assert pd.read_csv(out/name).trip_count.sum()==len(src)
CHECK={CASES[0]:c_style,CASES[1]:c_parallel,CASES[2]:c_rank,CASES[3]:c_reliability,CASES[4]:c_recovery}
def corrupt(case,source,dest):
 shutil.copytree(source,dest);p=dest/"data.csv";d=pd.read_csv(p);idcol="player_id" if "player_id" in d else "trip_id";d.loc[1,idcol]=d.loc[0,idcol];d.to_csv(p,index=False)
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix="inlumen-batch06-") as td:
  temp=Path(td)
  for case in CASES:
   source=ROOT/"pipelines"/case;v=validate(load(source/"task_graph.json"),source);out=temp/(case+"-out");run(case,source/"inputs",out);CHECK[case](source/"inputs",out);checks.append({"case":case,"probe":"reference_outputs_independent_invariants_and_topology","status":"passed","topology":v["topology"],"tasks":v["tasks"],"structure":v["structure"],"output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}});bad=temp/(case+"-bad");corrupt(case,source/"inputs",bad);run(case,bad,temp/(case+"-bad-out"),True);checks.append({"case":case,"probe":"invalid_identifier_rejected","status":"passed"})
   for track in ["natural_language","fixed_graph"]:
    dst=export(case,temp/f"{case}-{track}",track);files={str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file()};assert not any(Path(f).name in {"reference.py","task_graph.json","provenance.json","requirements.txt"} for f in files);assert ("provided_graph.json" in files)==(track=="fixed_graph")
  for case in CASES:
   g=load(ROOT/"pipelines"/case/"task_graph.json");wrong=copy.deepcopy(g);wrong["topology"]="linear" if g["topology"]!="linear" else "fan_out"
   try:validate(wrong)
   except AssertionError:pass
   else:raise AssertionError(case)
  checks.extend([{"case":"batch-06","probe":"incorrect_topology_labels_rejected","status":"passed"},{"case":"batch-06","probe":"generator_input_allowlist_both_tracks","status":"passed"}])
 report={"status":"passed","scope":"Batch-06 Python references, independent invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation","dagster_runtime_qualification":"not_run","review_status":"author_review_pending","python":sys.version.split()[0],"packages":{n:version(n) for n in ["pandas","numpy","scikit-learn","jsonschema"]},"checks":checks};(ROOT/"qualification-report-batch06.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({"status":"passed","check_groups":len(checks),"dagster_runtime_qualification":"not_run"},indent=2))
if __name__=="__main__":main()
