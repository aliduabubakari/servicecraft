"""Qualify batch 09."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['024_sports_regression_prediction_statistical','033_sports_statistical_cleaning_integration_v3','039_sports_statistical_visualization_cleaning','059_transportation_cleaning_integration_recovery','088_transportation_statistical_integration_v2']
def load(p):return json.loads(p.read_text(),parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def run(c,data,out,fail=False):
 out.mkdir();r=subprocess.run([sys.executable,str(ROOT/'pipelines'/c/'reference.py'),'--data-dir',str(data),'--output-dir',str(out)],capture_output=True,text=True)
 if fail:assert r.returncode!=0;return
 if r.returncode:raise RuntimeError(r.stderr)
 for x in load(ROOT/'pipelines'/c/'task_graph.json')['artifacts']:
  p=out/x['path'];assert p.is_file()
  if p.suffix=='.csv':assert set(x['required_columns'])<=set(pd.read_csv(p,nrows=0).columns)
  elif p.suffix=='.json':load(p)
def inspect(c,data,out):
 src=pd.read_csv(data/'data.csv')
 if c==CASES[0]:
  rp=pd.read_csv(out/'market_predictions.csv');cp=pd.read_csv(out/'allstar_predictions.csv');rm=load(out/'market_metrics.json');cm=load(out/'allstar_metrics.json');assert len(rp)==117 and len(cp)==146 and rm['test_rows']==117 and cm['test_rows']==146;assert cp.probability.between(0,1).all();assert set(cp.predicted_all_star)<= {0,1};assert np.isfinite(list(rm.values())).all() and np.isfinite(list(cm.values())).all()
 elif c==CASES[1]:
  scores=pd.read_csv(out/'player_scores.csv');rank=pd.read_csv(out/'ranked_players.csv');leaders=pd.read_csv(out/'position_leaders.csv');np.testing.assert_allclose(scores.shooting_index,scores[['field_goal_pct','three_point_pct','free_throw_pct']].mean(axis=1));assert rank['rank'].tolist()==list(range(1,len(src)+1));assert len(leaders)==3*src.position.nunique()
 elif c==CASES[2]:
  team=pd.read_csv(out/'team_summary.csv');pos=pd.read_csv(out/'position_summary.csv');age=pd.read_csv(out/'age_summary.csv');report=load(out/'sports_report.json');assert team.player_count.sum()==pos.player_count.sum()==age.player_count.sum()==len(src);assert report['players']==len(src)
 elif c==CASES[3]:
  clean=pd.read_csv(out/'trips_clean.csv');assert len(clean)==len(src);np.testing.assert_allclose(clean.passenger_km,clean.distance_km*clean.passengers);np.testing.assert_array_equal(clean.on_time.astype(bool),clean.delay_minutes.le(5));
  for f in ['route_operations.csv','vehicle_operations.csv','weather_operations.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 else:
  feat=pd.read_csv(out/'trip_service_features.csv');routes=pd.read_csv(out/'route_service_metrics.csv');rel=pd.read_csv(out/'reliability_ranking.csv');sat=pd.read_csv(out/'satisfaction_ranking.csv');assoc=load(out/'service_associations.json');np.testing.assert_allclose(feat.service_score,(feat.on_time_pct+feat.passenger_satisfaction/5)/2);assert routes.trip_count.sum()==len(src);assert len(rel)==len(sat)==len(routes)==assoc['routes']
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b9-') as td:
  temp=Path(td)
  for c in CASES:
   src=ROOT/'pipelines'/c;v=validate(load(src/'task_graph.json'),src);out=temp/(c+'-out');run(c,src/'inputs',out);inspect(c,src/'inputs',out);checks.append({'case':c,'probe':'reference_outputs_independent_invariants_and_topology','status':'passed','topology':v['topology'],'tasks':v['tasks'],'structure':v['structure'],'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}})
   bad=temp/(c+'-bad');shutil.copytree(src/'inputs',bad);p=bad/'data.csv';d=pd.read_csv(p);idc='player_id' if 'player_id'in d else 'trip_id';d.loc[1,idc]=d.loc[0,idc];d.to_csv(p,index=False);run(c,bad,temp/(c+'-bad-out'),True);checks.append({'case':c,'probe':'invalid_identifier_rejected','status':'passed'})
   for track in ['natural_language','fixed_graph']:
    dst=export(c,temp/f'{c}-{track}',track);files={str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()};assert not any(Path(f).name in {'reference.py','task_graph.json','provenance.json','requirements.txt'} for f in files);assert ('provided_graph.json'in files)==(track=='fixed_graph')
  for c in CASES:
   g=load(ROOT/'pipelines'/c/'task_graph.json');wrong=copy.deepcopy(g);wrong['topology']='linear' if g['topology']!='linear' else 'fan_out'
   try:validate(wrong)
   except AssertionError:pass
   else:raise AssertionError(c)
  checks.extend([{'case':'batch-09','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-09','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-09 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch09.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
