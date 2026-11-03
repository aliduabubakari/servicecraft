"""Qualify batch 14."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['026_sports_regression_prediction_statistical_v3','043_sports_visualization','062_transportation_cleaning_validation_features','071_transportation_prediction_statistical_cleaning','080_transportation_regression_cleaning_integration']
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
  perf=pd.read_csv(out/'performance_features.csv');avail=pd.read_csv(out/'availability_features.csv');model=pd.read_csv(out/'model_data.csv');rp=pd.read_csv(out/'market_predictions.csv');cp=pd.read_csv(out/'allstar_predictions.csv');rep=load(out/'dual_model_report.json');np.testing.assert_allclose(perf.production_index,perf.points_per_game+perf.assists_per_game+perf.rebounds_per_game);assert len(perf)==len(avail)==len(model)==len(src);assert len(rp)==rep['regression_test_rows']==119 and len(cp)==rep['classification_test_rows']==149;assert cp.probability.between(0,1).all()
 elif c==CASES[1]:
  prepared=pd.read_csv(out/'players_prepared.csv');summary=pd.read_csv(out/'team_summary.csv');rank=pd.read_csv(out/'team_ranking.csv');chart=pd.read_csv(out/'team_chart_data.csv');rep=load(out/'team_report.json');np.testing.assert_allclose(prepared.production_index,prepared.points_per_game+prepared.assists_per_game+prepared.rebounds_per_game);assert summary.player_count.sum()==rep['players']==len(src);assert rank['rank'].tolist()==chart['rank'].tolist()==list(range(1,len(rank)+1));assert rep['top_team']==rank.iloc[0].team
 elif c==CASES[2]:
  trips=pd.read_csv(out/'trips_prepared.csv');np.testing.assert_allclose(trips.passenger_km,trips.distance_km*trips.passengers);np.testing.assert_array_equal(trips.on_time.astype(bool),trips.delay_minutes.le(5));assert trips.time_period.nunique()==4
  for f in ['route_operations.csv','period_operations.csv','weather_operations.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 elif c==CASES[3]:
  pred=pd.read_csv(out/'delay_predictions.csv');metrics=load(out/'delay_metrics.json');service=pd.read_csv(out/'service_data.csv');routes=pd.read_csv(out/'route_service.csv');rep=load(out/'service_report.json');assert len(pred)==metrics['test_rows']==178 and pred.probability.between(0,1).all();assert len(service)==len(src) and routes.trip_count.sum()==rep['trips']==len(src);np.testing.assert_allclose(routes.service_score,(routes.mean_on_time+routes.mean_satisfaction/5)/2)
 else:
  rev=pd.read_csv(out/'revenue_features.csv');cost=pd.read_csv(out/'cost_features.csv');trips=pd.read_csv(out/'trip_economics.csv');routes=pd.read_csv(out/'route_economics.csv');rank=pd.read_csv(out/'route_ranking.csv');rep=load(out/'economics_report.json');assert len(rev)==len(cost)==len(trips)==len(src);np.testing.assert_allclose(trips.profit,trips.revenue-trips.operational_cost);assert routes.trip_count.sum()==rep['trips']==len(src);assert rank['rank'].tolist()==list(range(1,len(rank)+1)) and rep['top_route']==rank.iloc[0].route
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b14-') as td:
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
  checks.extend([{'case':'batch-14','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-14','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-14 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch14.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
