"""Qualify batch 10."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['016_sports_clustering_prediction_visualization','034_sports_statistical_cleaning_integration_v4','060_transportation_cleaning_integration_validation','076_transportation_prediction_visualization_geospatial','086_transportation_statistical_geospatial_validation']
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
  ass=pd.read_csv(out/'cluster_assignments.csv');prof=pd.read_csv(out/'cluster_profiles.csv');mix=pd.read_csv(out/'team_cluster_mix.csv');stars=pd.read_csv(out/'cluster_allstar_rates.csv');rep=load(out/'cluster_report.json');assert len(ass)==len(src) and set(ass.cluster)==set(range(4));assert prof.player_count.sum()==mix.player_count.sum()==stars.player_count.sum()==len(src)==rep['players'];np.testing.assert_allclose(mix.groupby('team').team_share.sum(),1)
 elif c==CASES[1]:
  scores=pd.read_csv(out/'player_scores.csv');rank=pd.read_csv(out/'ranked_players.csv');leaders=pd.read_csv(out/'position_leaders.csv');np.testing.assert_allclose(scores.shooting_index,scores[['field_goal_pct','three_point_pct','free_throw_pct']].mean(axis=1));assert rank['rank'].tolist()==list(range(1,len(src)+1));assert len(leaders)==3*src.position.nunique()
 elif c==CASES[2]:
  clean=pd.read_csv(out/'trips_clean.csv');np.testing.assert_allclose(clean.passenger_km,clean.distance_km*clean.passengers);np.testing.assert_array_equal(clean.on_time.astype(bool),clean.delay_minutes.le(5));
  for f in ['route_operations.csv','vehicle_operations.csv','weather_operations.csv']:assert pd.read_csv(out/f).trip_count.sum()==len(src)
 elif c==CASES[3]:
  pred=pd.read_csv(out/'delay_predictions.csv');metric=load(out/'delay_metrics.json');geo=pd.read_csv(out/'trip_geography.csv');routes=pd.read_csv(out/'route_geography.csv');report=load(out/'geography_report.json');assert len(pred)==metric['test_rows']==187 and pred.probability.between(0,1).all();assert len(geo)==len(src) and geo.geodesic_km.ge(0).all();assert routes.trip_count.sum()==report['trips']==len(src);np.testing.assert_allclose(routes.total_passenger_geodesic_km.sum(),geo.passenger_geodesic_km.sum())
 else:
  g=pd.read_csv(out/'route_geography.csv');s=pd.read_csv(out/'route_service.csv');ctx=pd.read_csv(out/'route_context.csv');score=pd.read_csv(out/'route_scores.csv');rank=pd.read_csv(out/'route_ranking.csv');rep=load(out/'route_report.json');assert g.geography_trip_count.sum()==s.service_trip_count.sum()==rep['trips']==len(src);assert len(ctx)==len(score)==len(rank)==src.route.nunique();assert score.route_score.between(0,1).all();assert rank['rank'].tolist()==list(range(1,len(rank)+1)) and rep['top_route']==rank.iloc[0].route
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b10-') as td:
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
  checks.extend([{'case':'batch-10','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-10','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Batch-10 references, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch10.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
