"""Qualify batch 12."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['027_sports_regression_prediction_visualization','036_sports_statistical_cleaning_validation','048_sports_visualization_integration_geospatial','066_transportation_integration_geospatial','082_transportation_regression_statistical_integration']
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
  perf=pd.read_csv(out/'performance_features.csv');ctx=pd.read_csv(out/'context_features.csv');model=pd.read_csv(out/'model_data.csv');rp=pd.read_csv(out/'market_predictions.csv');cp=pd.read_csv(out/'allstar_predictions.csv');rep=load(out/'dual_model_report.json');np.testing.assert_allclose(perf.production_index,perf.points_per_game+perf.assists_per_game+perf.rebounds_per_game);assert len(perf)==len(ctx)==len(model)==len(src);assert len(rp)==rep['regression_test_rows']==81 and len(cp)==rep['classification_test_rows']==101;assert cp.probability.between(0,1).all()
 elif c==CASES[1]:
  scores=pd.read_csv(out/'player_scores.csv');rank=pd.read_csv(out/'ranked_players.csv');leaders=pd.read_csv(out/'position_leaders.csv');np.testing.assert_allclose(scores.shooting_index,scores[['field_goal_pct','three_point_pct','free_throw_pct']].mean(axis=1));assert rank['rank'].tolist()==list(range(1,len(src)+1));assert len(leaders)==3*src.position.nunique()
 elif c==CASES[2]:
  p=pd.read_csv(out/'player_performance.csv');teams=pd.read_csv(out/'team_performance.csv');g=pd.read_csv(out/'player_geography.csv');regions=pd.read_csv(out/'region_summary.csv');pr=load(out/'performance_report.json');gr=load(out/'geography_report.json');assert teams.player_count.sum()==pr['players']==len(p)==len(src);assert regions.player_count.sum()==gr['players']==len(g)==len(src);assert len(teams)==src.team.nunique() and len(regions)==src.region.nunique()
 elif c==CASES[3]:
  trips=pd.read_csv(out/'trips_geographic.csv');assert len(trips)==len(src) and trips.geodesic_km.ge(0).all() and trips.time_period.nunique()==4;np.testing.assert_allclose(trips.passenger_geodesic_km,trips.geodesic_km*trips.passengers)
  for f in ['route_geography.csv','vehicle_geography.csv','period_geography.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 else:
  e=pd.read_csv(out/'route_economics.csv');s=pd.read_csv(out/'route_service.csv');ctx=pd.read_csv(out/'route_context.csv');score=pd.read_csv(out/'route_scores.csv');rank=pd.read_csv(out/'route_ranking.csv');rep=load(out/'route_report.json');assert e.economic_trip_count.sum()==s.service_trip_count.sum()==rep['trips']==len(src);assert len(ctx)==len(score)==len(rank)==src.route.nunique();assert score.route_score.between(0,1).all();assert rank['rank'].tolist()==list(range(1,len(rank)+1)) and rep['top_route']==rank.iloc[0].route
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b12-') as td:
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
  checks.extend([{'case':'batch-12','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-12','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-12 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch12.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
