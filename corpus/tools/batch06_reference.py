"""Trusted references for benchmark batch 06."""
import argparse,json,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,precision_score,recall_score,roc_auc_score,silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
def req(d,c,n):
    m=sorted(set(c)-set(d.columns))
    if m:raise ValueError(f"{n} missing {m}")
def nums(d,c,n):
    for x in c:d[x]=pd.to_numeric(d[x],errors="coerce")
    if not np.isfinite(d[c].to_numpy(float)).all():raise ValueError(f"{n} nonfinite")
def key(d,c,n):
    if not d[c].is_unique or d[c].astype(str).str.strip().eq("").any():raise ValueError(f"{n} key")

def style(data,out):
    d=pd.read_csv(data/"data.csv");base=["player_id","team","position"];shoot=["field_goal_pct","three_point_pct","free_throw_pct"];play=["points_per_game","assists_per_game","rebounds_per_game","play_style_score","efficiency_rating","usage_rate"]
    req(d,[*base,*shoot,*play],"data");key(d,"player_id","data");nums(d,shoot+play,"data");clean=d[[*base,*shoot,*play]].sort_values("player_id");clean.to_csv(out/"players_clean.csv",index=False)
    shooting=clean[["player_id",*shoot]].copy();shooting["shooting_composite"]=shooting[shoot].mean(axis=1);shooting.to_csv(out/"shooting_features.csv",index=False)
    playing=clean[["player_id",*play]].copy();playing["production_index"]=playing.points_per_game+playing.assists_per_game+playing.rebounds_per_game;playing.to_csv(out/"playmaking_features.csv",index=False)
    integrated=clean[base].merge(shooting,on="player_id",validate="one_to_one").merge(playing,on="player_id",validate="one_to_one").sort_values("player_id");integrated.to_csv(out/"style_features.csv",index=False)
    features=[*shoot,"shooting_composite",*play,"production_index"];scaler=StandardScaler();x=scaler.fit_transform(integrated[features]);km=KMeans(n_clusters=5,random_state=42,n_init=20,algorithm="lloyd").fit(x);order=np.lexsort((np.arange(5),km.cluster_centers_[:,features.index("usage_rate")],km.cluster_centers_[:,features.index("efficiency_rating")]));mapping={int(raw):int(label) for label,raw in enumerate(order)};assigned=integrated.copy();assigned["cluster"]=[mapping[int(v)] for v in km.labels_];assigned.to_csv(out/"player_clusters.csv",index=False)
    with (out/"cluster_model.pkl").open("wb") as h:pickle.dump({"scaler":scaler,"model":km,"mapping":mapping,"features":features},h)
    profile=assigned.groupby("cluster",as_index=False).agg(player_count=("player_id","size"),mean_shooting=("shooting_composite","mean"),mean_production=("production_index","mean"),mean_efficiency=("efficiency_rating","mean"),mean_usage=("usage_rate","mean")).sort_values("cluster");profile.to_csv(out/"cluster_profiles.csv",index=False)
    mix=assigned.groupby(["position","cluster"],as_index=False).size().rename(columns={"size":"player_count"});mix["position_share"]=mix.player_count/mix.groupby("position").player_count.transform("sum");mix.sort_values(["position","cluster"]).to_csv(out/"position_cluster_mix.csv",index=False)
    coords=PCA(n_components=2,random_state=42).fit_transform(x);scatter=pd.DataFrame({"player_id":integrated.player_id,"cluster":assigned.cluster,"pc1":coords[:,0],"pc2":coords[:,1]});scatter.to_csv(out/"cluster_scatter_data.csv",index=False)
    js(out/"style_report.json",{"players":len(assigned),"clusters":5,"silhouette_score":silhouette_score(x,km.labels_),"positions":mix.position.nunique(),"scatter_rows":len(scatter)})

def player_parallel(data,out):
    d=pd.read_csv(data/"data.csv");features=["games_played","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","injury_games_missed","contract_year","field_goal_pct","three_point_pct","free_throw_pct"];req(d,["player_id","team","position","all_star",*features],"data");key(d,"player_id","data");nums(d,["all_star",*features],"data")
    pred=d[["player_id","all_star",*features]].sort_values("player_id");pred.to_csv(out/"prediction_data.csv",index=False);train,test=train_test_split(pred,test_size=.25,random_state=42,stratify=pred.all_star);model=Pipeline([("scale",StandardScaler()),("model",LogisticRegression(C=1,solver="liblinear",max_iter=1000,random_state=42))]);model.fit(train[features],train.all_star);prob=model.predict_proba(test[features])[:,1];yp=(prob>=.5).astype(int)
    with (out/"all_star_model.pkl").open("wb") as h:pickle.dump(model,h)
    pd.DataFrame({"player_id":test.player_id,"actual":test.all_star,"probability":prob,"predicted":yp}).sort_values("player_id").to_csv(out/"all_star_predictions.csv",index=False);js(out/"all_star_report.json",{"train_rows":len(train),"test_rows":len(test),"accuracy":accuracy_score(test.all_star,yp),"precision":precision_score(test.all_star,yp,zero_division=0),"recall":recall_score(test.all_star,yp,zero_division=0),"f1":f1_score(test.all_star,yp,zero_division=0),"roc_auc":roc_auc_score(test.all_star,prob)})
    stats=d.groupby("position",as_index=False).agg(player_count=("player_id","size"),all_star_rate=("all_star","mean"),mean_points=("points_per_game","mean"),mean_salary=("salary_millions","mean"));stats.to_csv(out/"position_statistics.csv",index=False);js(out/"position_report.json",{"positions":len(stats),"players":int(stats.player_count.sum()),"highest_all_star_rate_position":stats.sort_values(["all_star_rate","position"],ascending=[False,True]).iloc[0].position})
    chart=d.groupby("team",as_index=False).agg(player_count=("player_id","size"),all_star_count=("all_star","sum"),mean_points=("points_per_game","mean"),mean_salary=("salary_millions","mean")).sort_values("team");chart.to_csv(out/"team_chart_data.csv",index=False);js(out/"team_chart_report.json",{"teams":len(chart),"players":int(chart.player_count.sum()),"all_stars":int(chart.all_star_count.sum())})

def ranking(data,out):
    d=pd.read_csv(data/"data.csv");cols=["player_id","team","position","games_played","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","field_goal_pct","three_point_pct","free_throw_pct"];req(d,cols,"data");key(d,"player_id","data");nums(d,cols[3:],"data");clean=d[cols].sort_values("player_id");clean.to_csv(out/"players_clean.csv",index=False)
    f=clean.copy();f["production_index"]=f.points_per_game+f.assists_per_game+f.rebounds_per_game;f["shooting_index"]=f[["field_goal_pct","three_point_pct","free_throw_pct"]].mean(axis=1);f["per_minute_production"]=f.production_index/f.minutes_per_game;f.to_csv(out/"player_features.csv",index=False)
    ranked=f.sort_values(["production_index","shooting_index","player_id"],ascending=[False,False,True]).reset_index(drop=True);ranked["overall_rank"]=np.arange(1,len(ranked)+1);ranked.to_csv(out/"ranked_players.csv",index=False)
    top=ranked.groupby("position",group_keys=False).head(5).sort_values(["position","overall_rank"]);top.to_csv(out/"top_players_by_position.csv",index=False);js(out/"ranking_report.json",{"players":len(ranked),"positions":top.position.nunique(),"top_rows":len(top),"overall_leader":ranked.iloc[0].player_id})

def reliability(data,out):
    d=pd.read_csv(data/"data.csv");cols=["trip_id","route","vehicle_type","distance_km","passengers","delay_minutes","on_time_pct","passenger_satisfaction"];req(d,cols,"data");key(d,"trip_id","data");nums(d,cols[3:],"data")
    rel=d.groupby("route",as_index=False).agg(trip_count=("trip_id","size"),mean_delay_minutes=("delay_minutes","mean"),mean_on_time_pct=("on_time_pct","mean"),delay_std=("delay_minutes",lambda s:s.std(ddof=1))).sort_values("route");rel.to_csv(out/"route_reliability.csv",index=False)
    sat=d.groupby("route",as_index=False).agg(trip_count=("trip_id","size"),mean_satisfaction=("passenger_satisfaction","mean"),mean_passengers=("passengers","mean"),mean_distance_km=("distance_km","mean")).sort_values("route");sat.to_csv(out/"route_satisfaction.csv",index=False)
    score=rel.merge(sat,on=["route","trip_count"],validate="one_to_one");score["reliability_score"]=score.mean_on_time_pct;score["satisfaction_score"]=score.mean_satisfaction/5;score["combined_score"]=(score.reliability_score+score.satisfaction_score)/2;score.to_csv(out/"route_scores.csv",index=False)
    ranked=score.sort_values(["combined_score","route"],ascending=[False,True]).reset_index(drop=True);ranked["rank"]=np.arange(1,len(ranked)+1);ranked.to_csv(out/"ranked_routes.csv",index=False);js(out/"route_report.json",{"routes":len(ranked),"trips":int(ranked.trip_count.sum()),"top_route":ranked.iloc[0].route,"top_score":ranked.iloc[0].combined_score})

def recovery(data,out):
    d=pd.read_csv(data/"data.csv");cols=["trip_id","route","vehicle_type","distance_km","passengers","fare_amount","delay_minutes","weather_condition"];req(d,cols,"data");key(d,"trip_id","data");original=d.copy();d["route"]=d.route.astype(str).str.strip();d["vehicle_type"]=d.vehicle_type.fillna("").astype(str).str.strip().replace("","Unknown");d["weather_condition"]=d.weather_condition.fillna("").astype(str).str.strip().replace("","Unknown")
    counts={}
    for c in ["passengers","fare_amount","delay_minutes"]:
        d[c]=pd.to_numeric(d[c],errors="coerce");missing=d[c].isna();counts[c]=int(missing.sum());med=d.groupby("route")[c].transform("median");d.loc[missing,c]=med[missing];d[c]=d[c].fillna(d[c].median()).fillna(0)
    d[cols].sort_values("trip_id").to_csv(out/"trips_recovered.csv",index=False);js(out/"recovery_audit.json",{"input_rows":len(original),"output_rows":len(d),"imputed_numeric":counts,"unknown_vehicle_type":int((d.vehicle_type=="Unknown").sum()),"unknown_weather_condition":int((d.weather_condition=="Unknown").sum())})
    d.groupby("route",as_index=False).agg(trip_count=("trip_id","size"),mean_passengers=("passengers","mean"),mean_fare=("fare_amount","mean"),mean_delay=("delay_minutes","mean")).sort_values("route").to_csv(out/"route_summary.csv",index=False)
    d.groupby("vehicle_type",as_index=False).agg(trip_count=("trip_id","size"),mean_distance=("distance_km","mean"),mean_passengers=("passengers","mean"),mean_delay=("delay_minutes","mean")).sort_values("vehicle_type").to_csv(out/"vehicle_summary.csv",index=False)
    d.groupby("weather_condition",as_index=False).agg(trip_count=("trip_id","size"),mean_delay=("delay_minutes","mean"),mean_fare=("fare_amount","mean")).sort_values("weather_condition").to_csv(out/"weather_summary.csv",index=False)

RUNNERS={"017_sports_clustering_statistical_visualization":style,"020_sports_prediction_statistical_visualization":player_parallel,"030_sports_statistical_cleaning":ranking,"084_transportation_statistical_cleaning_integration":reliability,"099_transportation_visualization_recovery_reporting":recovery}
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--data-dir",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
