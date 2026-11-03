"""Executable behavioral references for batch 18."""
import argparse,sys
from pathlib import Path
import numpy as np,pandas as pd
TOOLS=Path(__file__).resolve().parents[2]/'tools';sys.path.insert(0,str(TOOLS))
from batch11_reference import prediction_parallel
from batch16_reference import trip_fanout
from batch17_reference import recovery_linear,prediction_multiview

def recovery_fanout(data,out):
 d=pd.read_csv(data/'data.csv',keep_default_na=True);cols=['player_id','team','position','games_played','points_per_game','assists_per_game','rebounds_per_game','minutes_per_game','age','experience_years','salary_millions']
 if set(cols)-set(d):raise ValueError('columns')
 if not d.player_id.is_unique or d.player_id.astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in ['team','position']:d[c]=d[c].replace(r'^\s*$',np.nan,regex=True)
 nums=[c for c in cols if c not in {'player_id','team','position'}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 d['missing_points_input']=d.points_per_game.isna().astype(int);d['missing_salary_input']=d.salary_millions.isna().astype(int);d['missing_team_input']=d.team.isna().astype(int);d['missing_position_input']=d.position.isna().astype(int);flags=['missing_points_input','missing_salary_input','missing_team_input','missing_position_input'];d[[*cols,*flags]].sort_values('player_id').to_csv(out/'audited_players.csv',index=False)
 n=d.copy()
 for c in nums:
  mask=n[c].isna();group=n.groupby('position')[c].transform('median');n.loc[mask,c]=group[mask];n[c]=n[c].fillna(n[c].median())
 if not np.isfinite(n[nums].to_numpy(float)).all():raise ValueError('numeric recovery')
 n[[*cols,*flags]].sort_values('player_id').to_csv(out/'numeric_recovered.csv',index=False)
 for c in ['team','position']:
  mask=n[c].isna();counts=n[c].dropna().value_counts();mode=sorted(counts[counts==counts.max()].index.astype(str))[0];n.loc[mask,c]=mode
 n['age_band']=pd.cut(n.age,[0,24,29,34,np.inf],labels=['<=24','25-29','30-34','35+']).astype(str);n[[*cols,*flags,'age_band']].sort_values('player_id').to_csv(out/'players_recovered.csv',index=False)
 agg={'player_count':('player_id','size'),'mean_points':('points_per_game','mean'),'mean_salary':('salary_millions','mean'),'recovered_points':('missing_points_input','sum'),'recovered_salary':('missing_salary_input','sum'),'recovered_team':('missing_team_input','sum'),'recovered_position':('missing_position_input','sum')};n.groupby('team',as_index=False).agg(**agg).sort_values('team').to_csv(out/'team_summary.csv',index=False);n.groupby('position',as_index=False).agg(**agg).sort_values('position').to_csv(out/'position_summary.csv',index=False);n.groupby('age_band',as_index=False).agg(**agg).sort_values('age_band').to_csv(out/'age_summary.csv',index=False)

RUNNERS={'046_sports_visualization_cleaning_recovery_v2':recovery_linear,'049_sports_visualization_integration_recovery':recovery_fanout,'073_transportation_prediction_validation':prediction_parallel,'078_transportation_prediction_visualization_integration_v2':prediction_multiview,'092_transportation_visualization_cleaning_integration':trip_fanout}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
