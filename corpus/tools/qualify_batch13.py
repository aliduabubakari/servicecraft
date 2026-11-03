"""Qualify batch 13."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['028_sports_regression_prediction_visualization_v2','037_sports_statistical_integration','067_transportation_integration_validation','083_transportation_regression_visualization_integration','089_transportation_statistical_visualization_integration']
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
  perf=pd.read_csv(out/'performance_features.csv');ctx=pd.read_csv(out/'context_features.csv');model=pd.read_csv(out/'model_data.csv');pred=pd.read_csv(out/'market_predictions.csv');team=pd.read_csv(out/'team_diagnostics.csv');pos=pd.read_csv(out/'position_diagnostics.csv');rep=load(out/'valuation_report.json');np.testing.assert_allclose(perf.production_index,perf.points_per_game+perf.assists_per_game+perf.rebounds_per_game);assert len(perf)==len(ctx)==len(model)==len(src);assert len(pred)==rep['model_test_rows']==82;assert team.player_count.sum()==pos.player_count.sum()==rep['players']==len(src)
 elif c==CASES[1]:
  f=pd.read_csv(out/'player_features.csv');summary=pd.read_csv(out/'position_summary.csv');rank=pd.read_csv(out/'position_ranking.csv');rep=load(out/'position_report.json');np.testing.assert_allclose(f.production_index,f.points_per_game+f.assists_per_game+f.rebounds_per_game);assert summary.player_count.sum()==rep['players']==len(src);assert rank['rank'].tolist()==list(range(1,len(rank)+1)) and rep['top_position']==rank.iloc[0].position
 elif c==CASES[2]:
  clean=pd.read_csv(out/'trips_clean.csv');np.testing.assert_allclose(clean.passenger_km,clean.distance_km*clean.passengers);np.testing.assert_array_equal(clean.on_time.astype(bool),clean.delay_minutes.le(5));
  for f in ['route_operations.csv','weekday_operations.csv','weather_operations.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 elif c==CASES[3]:
  trips=pd.read_csv(out/'trip_economics.csv');routes=pd.read_csv(out/'route_economics.csv');rank=pd.read_csv(out/'route_profitability.csv');vehicle=pd.read_csv(out/'vehicle_economics.csv');weather=pd.read_csv(out/'weather_economics.csv');np.testing.assert_allclose(trips.profit,trips.revenue-trips.operational_cost);assert routes.trip_count.sum()==vehicle.trip_count.sum()==weather.trip_count.sum()==len(src);assert rank.profit_rank.tolist()==list(range(1,len(rank)+1)) and len(rank)==src.route.nunique()
 else:
  route=pd.read_csv(out/'route_service.csv');vehicle=pd.read_csv(out/'vehicle_service.csv');weather=pd.read_csv(out/'weather_service.csv');rep=load(out/'service_report.json');assert route.trip_count.sum()==vehicle.trip_count.sum()==weather.trip_count.sum()==rep['trips']==len(src);assert rep['routes']==len(route) and rep['vehicles']==len(vehicle) and rep['weather_conditions']==len(weather)
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b13-') as td:
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
  checks.extend([{'case':'batch-13','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-13','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-13 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch13.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
