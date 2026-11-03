"""Qualify batch 08."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['022_sports_prediction_visualization_cleaning','032_sports_statistical_cleaning_integration_v2','038_sports_statistical_integration_v2','056_transportation_cleaning','087_transportation_statistical_integration']
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
  pred=pd.read_csv(out/'predictions.csv');team=pd.read_csv(out/'team_diagnostics.csv');assert len(pred)==142 and team.test_count.sum()==len(pred) and load(out/'model_report.json')['predictions']==len(pred)
 elif c==CASES[1]:
  scores=pd.read_csv(out/'player_scores.csv');rank=pd.read_csv(out/'ranked_players.csv');leaders=pd.read_csv(out/'position_leaders.csv');np.testing.assert_allclose(scores.shooting_index,scores[['field_goal_pct','three_point_pct','free_throw_pct']].mean(axis=1));assert rank['rank'].tolist()==list(range(1,len(src)+1)) and len(leaders)==3*src.position.nunique()
 elif c==CASES[2]:
  t=pd.read_csv(out/'team_summary.csv');p=pd.read_csv(out/'position_summary.csv');a=pd.read_csv(out/'age_summary.csv');assert t.player_count.sum()==p.player_count.sum()==a.player_count.sum()==len(src)
 elif c==CASES[3]:
  for f in ['route_operations.csv','vehicle_operations.csv','weather_operations.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 else:
  f=pd.read_csv(out/'trip_service_features.csv');routes=pd.read_csv(out/'route_service_metrics.csv');r1=pd.read_csv(out/'reliability_ranking.csv');r2=pd.read_csv(out/'satisfaction_ranking.csv');np.testing.assert_allclose(f.service_score,(f.on_time_pct+f.passenger_satisfaction/5)/2);assert routes.trip_count.sum()==len(src) and len(r1)==len(r2)==len(routes)
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b8-') as td:
  temp=Path(td)
  for c in CASES:
   src=ROOT/'pipelines'/c;v=validate(load(src/'task_graph.json'),src);out=temp/(c+'-out');run(c,src/'inputs',out);inspect(c,src/'inputs',out);checks.append({'case':c,'probe':'reference_outputs_independent_invariants_and_topology','status':'passed','topology':v['topology'],'tasks':v['tasks'],'structure':v['structure'],'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}});bad=temp/(c+'-bad');shutil.copytree(src/'inputs',bad);p=bad/'data.csv';d=pd.read_csv(p);idc='player_id' if 'player_id'in d else 'trip_id';d.loc[1,idc]=d.loc[0,idc];d.to_csv(p,index=False);run(c,bad,temp/(c+'-bad-out'),True);checks.append({'case':c,'probe':'invalid_identifier_rejected','status':'passed'})
   for track in ['natural_language','fixed_graph']:
    dst=export(c,temp/f'{c}-{track}',track);files={str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()};assert not any(Path(f).name in {'reference.py','task_graph.json','provenance.json','requirements.txt'} for f in files);assert ('provided_graph.json'in files)==(track=='fixed_graph')
  for c in CASES:
   g=load(ROOT/'pipelines'/c/'task_graph.json');w=copy.deepcopy(g);w['topology']='linear' if g['topology']!='linear' else 'fan_out'
   try:validate(w)
   except AssertionError:pass
   else:raise AssertionError(c)
  checks.extend([{'case':'batch-08','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-08','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-08 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch08.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
