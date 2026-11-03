"""Qualify batch 11."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['025_sports_regression_prediction_statistical_v2','035_sports_statistical_cleaning_integration_v5','061_transportation_cleaning_v2','068_transportation_prediction_cleaning','081_transportation_regression_statistical_cleaning']
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
  perf=pd.read_csv(out/'performance_features.csv');avail=pd.read_csv(out/'availability_features.csv');model=pd.read_csv(out/'model_data.csv');rp=pd.read_csv(out/'market_predictions.csv');cp=pd.read_csv(out/'allstar_predictions.csv');rep=load(out/'dual_model_report.json');np.testing.assert_allclose(perf.production_index,perf.points_per_game+perf.assists_per_game+perf.rebounds_per_game);assert len(perf)==len(avail)==len(model)==len(src);assert len(rp)==rep['regression_test_rows']==118 and len(cp)==rep['classification_test_rows']==147;assert cp.probability.between(0,1).all()
 elif c==CASES[1]:
  scores=pd.read_csv(out/'player_scores.csv');rank=pd.read_csv(out/'ranked_players.csv');leaders=pd.read_csv(out/'position_leaders.csv');np.testing.assert_allclose(scores.shooting_index,scores[['field_goal_pct','three_point_pct','free_throw_pct']].mean(axis=1));assert rank['rank'].tolist()==list(range(1,len(src)+1));assert len(leaders)==3*src.position.nunique()
 elif c==CASES[2]:
  clean=pd.read_csv(out/'trips_clean.csv');np.testing.assert_allclose(clean.passenger_km,clean.distance_km*clean.passengers);np.testing.assert_array_equal(clean.on_time.astype(bool),clean.delay_minutes.le(5));
  for f in ['route_operations.csv','vehicle_operations.csv','weather_operations.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 elif c==CASES[3]:
  dp=pd.read_csv(out/'delay_predictions.csv');rp=pd.read_csv(out/'risk_predictions.csv');dm=load(out/'delay_metrics.json');rm=load(out/'risk_metrics.json');assert len(dp)==len(rp)==dm['test_rows']==rm['test_rows']==173;assert dp.probability.between(0,1).all();assert np.isfinite(list(dm.values())).all() and np.isfinite(list(rm.values())).all()
 else:
  trips=pd.read_csv(out/'trip_economics.csv');routes=pd.read_csv(out/'route_metrics.csv');pr=pd.read_csv(out/'profitability_ranking.csv');sr=pd.read_csv(out/'service_ranking.csv');trade=load(out/'route_tradeoffs.json');np.testing.assert_allclose(trips.profit,trips.revenue-trips.operational_cost);np.testing.assert_allclose(trips.service_score,(trips.on_time_pct+trips.passenger_satisfaction/5)/2);assert routes.trip_count.sum()==trade['trips']==len(src);assert len(pr)==len(sr)==len(routes)==trade['routes'];assert pr.profit_rank.tolist()==sr.service_rank.tolist()==list(range(1,len(routes)+1))
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b11-') as td:
  temp=Path(td)
  for c in CASES:
   src=ROOT/'pipelines'/c;v=validate(load(src/'task_graph.json'),src);out=temp/(c+'-out');run(c,src/'inputs',out);inspect(c,src/'inputs',out);checks.append({'case':c,'probe':'reference_outputs_independent_invariants_and_topology','status':'passed','topology':v['topology'],'tasks':v['tasks'],'structure':v['structure'],'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}})
   bad=temp/(c+'-bad');shutil.copytree(src/'inputs',bad);p=bad/'data.csv';d=pd.read_csv(p);idc='player_id' if 'player_id' in d else 'trip_id';d.loc[1,idc]=d.loc[0,idc];d.to_csv(p,index=False);run(c,bad,temp/(c+'-bad-out'),True);checks.append({'case':c,'probe':'invalid_identifier_rejected','status':'passed'})
   for track in ['natural_language','fixed_graph']:
    dst=export(c,temp/f'{c}-{track}',track);files={str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()};assert not any(Path(f).name in {'reference.py','task_graph.json','provenance.json','requirements.txt'} for f in files);assert ('provided_graph.json' in files)==(track=='fixed_graph')
  for c in CASES:
   g=load(ROOT/'pipelines'/c/'task_graph.json');wrong=copy.deepcopy(g);wrong['topology']='linear' if g['topology']!='linear' else 'fan_out'
   try:validate(wrong)
   except AssertionError:pass
   else:raise AssertionError(c)
  checks.extend([{'case':'batch-11','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-11','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-11 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch11.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
