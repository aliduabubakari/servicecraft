"""Executable behavioral references for batch 15."""
import argparse,pickle,sys
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
TOOLS=Path(__file__).resolve().parents[2]/'tools';sys.path.insert(0,str(TOOLS))
from batch08_reference import js
from batch13_reference import trip_fanout
from batch14_reference import team_linear,prediction_service_parallel

def valid(d,cols,idc,cats=()):
 if set(cols)-set(d):raise ValueError('columns')
 if not d[idc].is_unique or d[idc].astype(str).str.strip().eq('').any():raise ValueError('id')
 for c in cats:
  if d[c].isna().any() or d[c].astype(str).str.strip().eq('').any():raise ValueError('category')
 nums=[c for c in cols if c not in {idc,*cats}]
 for c in nums:d[c]=pd.to_numeric(d[c],errors='coerce')
 if not np.isfinite(d[nums].to_numpy(float)).all():raise ValueError('nonfinite')

def haversine(lat1,lon1,lat2,lon2):
 p1,p2=np.radians(lat1),np.radians(lat2);dp=np.radians(lat2-lat1);dl=np.radians(lon2-lon1);a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2;return 6371.0088*2*np.arctan2(np.sqrt(a),np.sqrt(1-a))

def valuation_multiview(data,out):
 d=pd.read_csv(data/'data.csv');cols=['player_id','team','position','games_played','points_per_game','assists_per_game','rebounds_per_game','minutes_per_game','age','experience_years','salary_millions','market_value','win_shares','field_goal_pct','three_point_pct','free_throw_pct'];valid(d,cols,'player_id',['team','position']);d=d[cols].sort_values('player_id');d.to_csv(out/'players_clean.csv',index=False)
 p=d[['player_id','points_per_game','assists_per_game','rebounds_per_game','minutes_per_game','win_shares']].copy();p['production_index']=p.points_per_game+p.assists_per_game+p.rebounds_per_game;p['production_per_minute']=np.where(p.minutes_per_game>0,p.production_index/p.minutes_per_game,0);p.to_csv(out/'production_features.csv',index=False)
 s=d[['player_id','field_goal_pct','three_point_pct','free_throw_pct']].copy();s['shooting_index']=s[['field_goal_pct','three_point_pct','free_throw_pct']].mean(axis=1);s['weighted_shooting_index']=.5*s.field_goal_pct+.3*s.three_point_pct+.2*s.free_throw_pct;s.to_csv(out/'shooting_features.csv',index=False)
 c=d[['player_id','team','position','games_played','age','experience_years','salary_millions','market_value']].copy();c['salary_per_game']=np.where(c.games_played>0,c.salary_millions/c.games_played,0);c.to_csv(out/'context_features.csv',index=False);m=p.merge(s,on='player_id',validate='one_to_one').merge(c,on='player_id',validate='one_to_one');m.to_csv(out/'model_data.csv',index=False);features=['production_index','production_per_minute','minutes_per_game','win_shares','shooting_index','weighted_shooting_index','age','experience_years','salary_millions','salary_per_game'];tr,te=train_test_split(m,test_size=.2,random_state=42);model=Pipeline([('scale',StandardScaler()),('model',Ridge(alpha=1))]);model.fit(tr[features],tr.market_value);pred=model.predict(te[features])
 with (out/'valuation_model.pkl').open('wb') as h:pickle.dump(model,h)
 pd.DataFrame({'player_id':te.player_id,'actual_market_value':te.market_value,'predicted_market_value':pred}).sort_values('player_id').to_csv(out/'valuation_predictions.csv',index=False);js(out/'valuation_metrics.json',{'train_rows':len(tr),'test_rows':len(te),'mae':mean_absolute_error(te.market_value,pred),'rmse':mean_squared_error(te.market_value,pred)**.5,'r2':r2_score(te.market_value,pred)})
 team=m.groupby('team',as_index=False).agg(player_count=('player_id','size'),mean_market_value=('market_value','mean'),mean_production=('production_index','mean'),mean_shooting=('shooting_index','mean'),mean_salary=('salary_millions','mean')).sort_values('team');team.to_csv(out/'team_diagnostics.csv',index=False);pos=m.groupby('position',as_index=False).agg(player_count=('player_id','size'),mean_market_value=('market_value','mean'),mean_production=('production_index','mean'),mean_shooting=('shooting_index','mean'),mean_win_shares=('win_shares','mean')).sort_values('position');pos.to_csv(out/'position_diagnostics.csv',index=False);js(out/'valuation_report.json',{'players':len(m),'model_test_rows':len(te),'team_players':int(team.player_count.sum()),'position_players':int(pos.player_count.sum()),'teams':len(team),'positions':len(pos)})

def geo_ltof(data,out):
 d=pd.read_csv(data/'data.csv');cols=['trip_id','route','vehicle_type','departure_hour','distance_km','passengers','fare_amount','delay_minutes','day_of_week','is_holiday','weather_condition','origin_lat','origin_lon','dest_lat','dest_lon'];valid(d,cols,'trip_id',['route','vehicle_type','day_of_week','weather_condition']);assert d.origin_lat.between(-90,90).all() and d.dest_lat.between(-90,90).all() and d.origin_lon.between(-180,180).all() and d.dest_lon.between(-180,180).all();clean=d[cols].sort_values('trip_id');clean.to_csv(out/'trips_clean.csv',index=False);g=clean.copy();g['geodesic_km']=haversine(g.origin_lat,g.origin_lon,g.dest_lat,g.dest_lon);g['passenger_geodesic_km']=g.geodesic_km*g.passengers;g['time_period']=pd.cut(g.departure_hour,[-1,5,11,17,23],labels=['night','morning','afternoon','evening']).astype(str);g.to_csv(out/'trip_geography.csv',index=False);routes=g.groupby('route',as_index=False).agg(trip_count=('trip_id','size'),mean_geodesic_km=('geodesic_km','mean'),total_passenger_geodesic_km=('passenger_geodesic_km','sum'),mean_delay=('delay_minutes','mean')).sort_values('route');routes.to_csv(out/'route_geography.csv',index=False);rank=routes.sort_values(['total_passenger_geodesic_km','mean_geodesic_km','route'],ascending=[False,False,True]).reset_index(drop=True);rank.insert(1,'rank',np.arange(1,len(rank)+1));rank.to_csv(out/'route_geography_ranking.csv',index=False);g.groupby('vehicle_type',as_index=False).agg(trip_count=('trip_id','size'),mean_geodesic_km=('geodesic_km','mean'),mean_passengers=('passengers','mean'),mean_fare=('fare_amount','mean')).sort_values('vehicle_type').to_csv(out/'vehicle_geography.csv',index=False);g.groupby('time_period',as_index=False).agg(trip_count=('trip_id','size'),mean_geodesic_km=('geodesic_km','mean'),mean_delay=('delay_minutes','mean'),total_passengers=('passengers','sum')).sort_values('time_period').to_csv(out/'period_geography.csv',index=False)

RUNNERS={'029_sports_regression_statistical_visualization':valuation_multiview,'044_sports_visualization_cleaning_integration':team_linear,'064_transportation_integration':trip_fanout,'072_transportation_prediction_statistical_integration':prediction_service_parallel,'095_transportation_visualization_geospatial':geo_ltof}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
