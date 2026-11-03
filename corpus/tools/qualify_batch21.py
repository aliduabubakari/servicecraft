"""Qualify the final partial batch 21."""
import copy,hashlib,json,shutil,subprocess,sys,tempfile
from importlib.metadata import version
from pathlib import Path
import numpy as np,pandas as pd
from export_inputs import export
from validate_specs import ROOT,validate
CASES=['053_sports_visualization_validation_recovery','100_transportation_visualization_v2']
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
  audited=pd.read_csv(out/'audited_players.csv');recovered=pd.read_csv(out/'players_recovered.csv');team=pd.read_csv(out/'team_summary.csv');pos=pd.read_csv(out/'position_summary.csv');age=pd.read_csv(out/'age_summary.csv');assert audited[['missing_points_input','missing_salary_input','missing_team_input','missing_position_input']].sum().sum()==4;assert recovered.notna().all().all();assert team.player_count.sum()==pos.player_count.sum()==age.player_count.sum()==len(src);assert team[['recovered_points','recovered_salary','recovered_team','recovered_position']].sum().sum()==4
 else:
  trips=pd.read_csv(out/'trips_prepared.csv');summary=pd.read_csv(out/'route_summary.csv');rank=pd.read_csv(out/'route_ranking.csv');chart=pd.read_csv(out/'route_chart_data.csv');rep=load(out/'route_report.json');np.testing.assert_allclose(trips.passenger_km,trips.distance_km*trips.passengers);np.testing.assert_array_equal(trips.on_time.astype(bool),trips.delay_minutes.le(5));assert summary.trip_count.sum()==rep['trips']==len(src);assert rank['rank'].tolist()==chart['rank'].tolist()==list(range(1,len(rank)+1));assert rep['top_route']==rank.iloc[0].route
def main():
 checks=[]
 with tempfile.TemporaryDirectory(prefix='inlumen-b21-') as td:
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
  checks.extend([{'case':'batch-21','probe':'incorrect_topology_labels_rejected','status':'passed'},{'case':'batch-21','probe':'generator_input_allowlist_both_tracks','status':'passed'}])
 report={'status':'passed','scope':'Final partial Batch-21 references, recovery behavior, invariants, invalid-ID rejection, topology classification, graph consistency, and export allowlists; not Dagster execution','partial_final_batch':True,'dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],'packages':{n:version(n) for n in ['pandas','numpy','scikit-learn','jsonschema']},'checks':checks};(ROOT/'qualification-report-batch21.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':'passed','check_groups':len(checks),'partial_final_batch':True,'dagster_runtime_qualification':'not_run'},indent=2))
if __name__=='__main__':main()
