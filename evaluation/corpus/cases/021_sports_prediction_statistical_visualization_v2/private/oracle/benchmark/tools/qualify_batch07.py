"""Qualify batch 07."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=["018_sports_clustering_visualization_integration","021_sports_prediction_statistical_visualization_v2","031_sports_statistical_cleaning_integration","057_transportation_cleaning_integration","085_transportation_statistical_geospatial"]
def load(p):
 def bad(v):raise ValueError(v)
 return json.loads(p.read_text(),parse_constant=bad)
def run(c,data,out,fail=False):
 out.mkdir();r=subprocess.run([sys.executable,str(ROOT/"pipelines"/c/"reference.py"),"--data-dir",str(data),"--output-dir",str(out)],capture_output=True,text=True)
 if fail:assert r.returncode!=0;return
 if r.returncode:raise RuntimeError(r.stderr)
 for x in load(ROOT/"pipelines"/c/"task_graph.json")["artifacts"]:
  p=out/x["path"];assert p.is_file()
  if p.suffix==".csv":assert set(x["required_columns"])<=set(pd.read_csv(p,nrows=0).columns)
  elif p.suffix==".json":load(p)
def check(c,data,out):
 src=pd.read_csv(data/"data.csv")
 if c==CASES[0]:
  cl=pd.read_csv(out/"player_clusters.csv");pr=pd.read_csv(out/"cluster_profiles.csv");mix=pd.read_csv(out/"team_cluster_mix.csv");plot=pd.read_csv(out/"cluster_plot_data.csv");assert len(cl)==len(plot)==len(src) and pr.player_count.sum()==len(src);np.testing.assert_allclose(mix.groupby("team").team_share.sum(),1)
 elif c==CASES[1]:
  pred=pd.read_csv(out/"predictions.csv");pos=pd.read_csv(out/"position_model_summary.csv");cal=pd.read_csv(out/"calibration_bins.csv");rep=load(out/"allstar_report.json");assert len(pred)==140 and pos.test_count.sum()==len(pred) and cal['count'].sum()==len(pred) and rep["predictions"]==len(pred)
 elif c==CASES[2]:
  team=pd.read_csv(out/"team_production.csv");pos=pd.read_csv(out/"position_shooting.csv");exp=pd.read_csv(out/"experience_summary.csv");rep=load(out/"sports_summary_report.json");assert team.player_count.sum()==pos.player_count.sum()==exp.player_count.sum()==len(src) and rep["players"]==len(src)
 elif c==CASES[3]:
  f=pd.read_csv(out/"trip_features.csv");rank=pd.read_csv(out/"ranked_routes.csv");np.testing.assert_allclose(f.passenger_km,f.passengers*f.distance_km);assert rank.trip_count.sum()==len(src) and load(out/"route_performance_report.json")["top_route"]==rank.iloc[0].route
 else:
  spatial=pd.read_csv(out/"trip_spatial_metrics.csv");rs=pd.read_csv(out/"route_spatial_summary.csv");service=pd.read_csv(out/"trip_service_metrics.csv");sg=pd.read_csv(out/"service_group_summary.csv");assert len(spatial)==len(service)==len(src) and rs.trip_count.sum()==sg.trip_count.sum()==len(src);assert (spatial.great_circle_km>=0).all()
def corrupt(c,source,dest):
 shutil.copytree(source,dest);p=dest/"data.csv";d=pd.read_csv(p);idc="player_id" if "player_id" in d else "trip_id";d.loc[1,idc]=d.loc[0,idc];d.to_csv(p,index=False)
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix="inlumen-batch07-") as td:
  temp=Path(td)
  for c in CASES:
   source=ROOT/"pipelines"/c;v=validate(load(source/"task_graph.json"),source);out=temp/(c+"-out");run(c,source/"inputs",out);check(c,source/"inputs",out);checks.append({"case":c,"probe":"reference_outputs_independent_invariants_and_topology","status":"passed","topology":v["topology"],"tasks":v["tasks"],"structure":v["structure"],"output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}});bad=temp/(c+"-bad");corrupt(c,source/"inputs",bad);run(c,bad,temp/(c+"-bad-out"),True);checks.append({"case":c,"probe":"invalid_identifier_rejected","status":"passed"})
   for track in ["natural_language","fixed_graph"]:
    dst=export(c,temp/f"{c}-{track}",track);files={str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file()};assert not any(Path(f).name in {"reference.py","task_graph.json","provenance.json","requirements.txt"} for f in files);assert ("provided_graph.json" in files)==(track=="fixed_graph")
  for c in CASES:
   g=load(ROOT/"pipelines"/c/"task_graph.json");w=copy.deepcopy(g);w["topology"]="linear" if g["topology"]!="linear" else "fan_in"
   try:validate(w)
   except AssertionError:pass
   else:raise AssertionError(c)
  checks.extend([{"case":"batch-07","probe":"incorrect_topology_labels_rejected","status":"passed"},{"case":"batch-07","probe":"generator_input_allowlist_both_tracks","status":"passed"}])
 report={"status":"passed","scope":"Batch-07 Python references, independent invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation","dagster_runtime_qualification":"not_run","review_status":"author_review_pending","python":sys.version.split()[0],"packages":{n:version(n) for n in ["pandas","numpy","scikit-learn","jsonschema"]},"checks":checks};(ROOT/"qualification-report-batch07.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({"status":"passed","check_groups":len(checks),"dagster_runtime_qualification":"not_run"},indent=2))
if __name__=="__main__":main()
