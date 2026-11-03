"""Trusted references for topology-diverse benchmark batch 05."""
import argparse,json,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression,LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,mean_absolute_error,mean_squared_error,precision_score,recall_score,roc_auc_score,silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def js(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")
def req(d,cols,name):
    missing=sorted(set(cols)-set(d.columns))
    if missing:raise ValueError(f"{name} missing {missing}")
    if d.empty:raise ValueError(f"{name} empty")
def nums(d,cols,name):
    for c in cols:d[c]=pd.to_numeric(d[c],errors="coerce")
    if not np.isfinite(d[cols].to_numpy(float)).all():raise ValueError(f"{name} non-finite values")
def key(d,col,name):
    if not d[col].is_unique or d[col].astype(str).str.strip().eq("").any():raise ValueError(f"{name} invalid {col}")

def experiment(data,out):
    d=pd.read_csv(data/"data.csv");cols=["subject_id","group","baseline_score","post_score","age","region","sessions_attended","outcome"];req(d,cols,"data.csv");key(d,"subject_id","data.csv");nums(d,["baseline_score","post_score","age","sessions_attended","outcome"],"data.csv")
    if not d[["baseline_score","post_score"]].apply(lambda s:s.between(0,100)).all().all() or not set(d.outcome.unique())<={0,1}:raise ValueError("score/outcome bounds")
    clean=d[cols].sort_values("subject_id");clean.to_csv(out/"subjects_clean.csv",index=False)
    changes=clean.copy();changes["score_change"]=changes.post_score-changes.baseline_score;changes["improved"]=((changes.score_change>0)).astype(int);changes.to_csv(out/"subject_changes.csv",index=False)
    summary=changes.groupby("group",as_index=False).agg(subject_count=("subject_id","size"),mean_baseline=("baseline_score","mean"),mean_post=("post_score","mean"),mean_change=("score_change","mean"),std_change=("score_change",lambda s:s.std(ddof=1)),improvement_rate=("improved","mean"),outcome_rate=("outcome","mean")).sort_values("group");summary.to_csv(out/"group_summary.csv",index=False)
    indexed=summary.set_index("group");control=indexed.loc["Control"];rows=[]
    for group in sorted(set(summary.group)-{"Control"}):
        values=indexed.loc[group];difference=values.mean_change-control.mean_change;se=np.sqrt(values.std_change**2/values.subject_count+control.std_change**2/control.subject_count);rows.append([group,int(values.subject_count),int(control.subject_count),difference,se,difference-1.96*se,difference+1.96*se])
    contrasts=pd.DataFrame(rows,columns=["treatment_group","treatment_n","control_n","difference_in_mean_change","standard_error","ci95_low","ci95_high"]);contrasts.to_csv(out/"treatment_contrasts.csv",index=False)
    context={"subjects":int(summary.subject_count.sum()),"groups":len(summary),"overall_mean_change":np.average(summary.mean_change,weights=summary.subject_count),"overall_improvement_rate":np.average(summary.improvement_rate,weights=summary.subject_count),"largest_mean_change_group":summary.sort_values(["mean_change","group"],ascending=[False,True]).iloc[0].group,"contrasts":len(contrasts)};js(out/"contrast_context.json",context);js(out/"experiment_report.json",context)

def sports_fanout(data,out):
    d=pd.read_csv(data/"data.csv");cols=["player_id","team","position","games_played","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","all_star","injury_games_missed","contract_year"];req(d,cols,"data.csv");key(d,"player_id","data.csv");nums(d,cols[3:],"data.csv")
    if not set(d.all_star.unique())<={0,1}:raise ValueError("all_star binary")
    clean=d[cols].sort_values("player_id");clean["availability_rate"]=(clean.games_played-clean.injury_games_missed).clip(lower=0)/clean.games_played;clean["salary_per_point"]=np.where(clean.points_per_game>0,clean.salary_millions/clean.points_per_game,np.nan);clean.to_csv(out/"players_clean.csv",index=False)
    features=["games_played","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","injury_games_missed","contract_year"]
    train,test=train_test_split(clean,test_size=.25,random_state=42,stratify=clean.all_star);model=Pipeline([("scale",StandardScaler()),("model",LogisticRegression(C=1,solver="liblinear",max_iter=1000,random_state=42))]);model.fit(train[features],train.all_star);prob=model.predict_proba(test[features])[:,1];pred=(prob>=.5).astype(int)
    with (out/"all_star_model.pkl").open("wb") as h:pickle.dump(model,h)
    pd.DataFrame({"player_id":test.player_id,"actual_all_star":test.all_star,"probability":prob,"predicted_all_star":pred}).sort_values("player_id").to_csv(out/"all_star_predictions.csv",index=False)
    js(out/"all_star_metrics.json",{"train_rows":len(train),"test_rows":len(test),"features":features,"accuracy":accuracy_score(test.all_star,pred),"precision":precision_score(test.all_star,pred,zero_division=0),"recall":recall_score(test.all_star,pred,zero_division=0),"f1":f1_score(test.all_star,pred,zero_division=0),"roc_auc":roc_auc_score(test.all_star,prob)})
    clean.groupby("team",as_index=False).agg(player_count=("player_id","size"),mean_games_played=("games_played","mean"),mean_injury_games_missed=("injury_games_missed","mean"),mean_availability_rate=("availability_rate","mean")).sort_values("team").to_csv(out/"team_availability.csv",index=False)
    clean.groupby("position",as_index=False).agg(player_count=("player_id","size"),mean_salary_millions=("salary_millions","mean"),mean_points_per_game=("points_per_game","mean"),mean_salary_per_point=("salary_per_point","mean")).sort_values("position").to_csv(out/"position_compensation.csv",index=False)

def sports_parallel(data,out):
    d=pd.read_csv(data/"data.csv");base=["player_id","team","position"];reg=["games_played","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","efficiency_rating","usage_rate","win_shares"];clu=["points_per_game","assists_per_game","rebounds_per_game","play_style_score","efficiency_rating","usage_rate"]
    req(d,[*base,*reg,*clu,"market_value"],"data.csv");key(d,"player_id","data.csv");nums(d,list(set(reg+clu+["market_value"])),"data.csv")
    regression=d[["player_id","market_value",*reg]].sort_values("player_id");regression.to_csv(out/"regression_features.csv",index=False);train,test=train_test_split(regression,test_size=.2,random_state=42);model=Pipeline([("scale",StandardScaler()),("model",LinearRegression())]);model.fit(train[reg],train.market_value);pred=model.predict(test[reg])
    with (out/"market_value_model.pkl").open("wb") as h:pickle.dump(model,h)
    pd.DataFrame({"player_id":test.player_id,"actual_market_value":test.market_value,"predicted_market_value":pred}).sort_values("player_id").to_csv(out/"market_value_predictions.csv",index=False);js(out/"market_value_metrics.json",{"train_rows":len(train),"test_rows":len(test),"features":reg,"mae":mean_absolute_error(test.market_value,pred),"rmse":mean_squared_error(test.market_value,pred)**.5,"r2":model.score(test[reg],test.market_value)})
    clustering=d[[*base,*clu]].sort_values("player_id");clustering.to_csv(out/"clustering_features.csv",index=False);scaler=StandardScaler();x=scaler.fit_transform(clustering[clu]);km=KMeans(n_clusters=4,random_state=42,n_init=20,algorithm="lloyd").fit(x);order=np.lexsort((np.arange(4),km.cluster_centers_[:,clu.index("usage_rate")],km.cluster_centers_[:,clu.index("efficiency_rating")]));mapping={int(raw):int(label) for label,raw in enumerate(order)};assigned=clustering.copy();assigned["cluster"]=[mapping[int(v)] for v in km.labels_];assigned.to_csv(out/"player_clusters.csv",index=False)
    with (out/"cluster_model.pkl").open("wb") as h:pickle.dump({"scaler":scaler,"model":km,"mapping":mapping,"features":clu},h)
    profile=assigned.groupby("cluster",as_index=False).agg(player_count=("player_id","size"),mean_points=("points_per_game","mean"),mean_assists=("assists_per_game","mean"),mean_rebounds=("rebounds_per_game","mean"),mean_efficiency=("efficiency_rating","mean"),mean_usage=("usage_rate","mean")).sort_values("cluster");profile.to_csv(out/"cluster_profiles.csv",index=False);js(out/"cluster_report.json",{"players":len(assigned),"clusters":4,"silhouette_score":silhouette_score(x,km.labels_)})

def transport_cluster(data,out):
    d=pd.read_csv(data/"data.csv");cols=["trip_id","route","vehicle_type","departure_hour","distance_km","passengers","fare_amount","delay_minutes","day_of_week","is_holiday","weather_condition","peak_hour","avg_load_factor"];req(d,cols,"data.csv");key(d,"trip_id","data.csv");nums(d,["departure_hour","distance_km","passengers","fare_amount","delay_minutes","is_holiday","peak_hour","avg_load_factor"],"data.csv")
    if not set(d.is_holiday.unique())<={0,1} or not set(d.peak_hour.unique())<={0,1}:raise ValueError("flags binary")
    clean=d[cols].sort_values("trip_id");clean.to_csv(out/"trips_clean.csv",index=False);features=["departure_hour","distance_km","passengers","fare_amount","delay_minutes","is_holiday","peak_hour","avg_load_factor"];prepared=clean[["trip_id","route","vehicle_type",*features]];prepared.to_csv(out/"clustering_features.csv",index=False)
    scaler=StandardScaler();x=scaler.fit_transform(prepared[features]);km=KMeans(n_clusters=5,random_state=42,n_init=20,algorithm="lloyd").fit(x);order=np.lexsort((np.arange(5),km.cluster_centers_[:,features.index("delay_minutes")],km.cluster_centers_[:,features.index("avg_load_factor")]));mapping={int(raw):int(label) for label,raw in enumerate(order)};assigned=prepared.copy();assigned["cluster"]=[mapping[int(v)] for v in km.labels_];assigned.to_csv(out/"trip_clusters.csv",index=False)
    with (out/"cluster_model.pkl").open("wb") as h:pickle.dump({"scaler":scaler,"model":km,"mapping":mapping,"features":features},h)
    assigned.groupby("cluster",as_index=False).agg(trip_count=("trip_id","size"),mean_distance_km=("distance_km","mean"),mean_passengers=("passengers","mean"),mean_delay_minutes=("delay_minutes","mean"),mean_load_factor=("avg_load_factor","mean")).sort_values("cluster").to_csv(out/"cluster_profiles.csv",index=False)
    route_mix=assigned.groupby(["route","cluster"],as_index=False).size().rename(columns={"size":"trip_count"});route_total=route_mix.groupby("route").trip_count.transform("sum");route_mix["route_share"]=route_mix.trip_count/route_total;route_mix.sort_values(["route","cluster"]).to_csv(out/"route_cluster_mix.csv",index=False)
    js(out/"cluster_validation.json",{"trips":len(assigned),"clusters":5,"silhouette_score":silhouette_score(x,km.labels_),"inertia":km.inertia_,"cluster_sizes":{str(k):int(v) for k,v in assigned.cluster.value_counts().sort_index().items()}})

def economics(data,out):
    d=pd.read_csv(data/"data.csv");cols=["trip_id","route","vehicle_type","departure_hour","distance_km","passengers","fare_amount","delay_minutes","day_of_week","is_holiday","weather_condition","revenue","operational_cost"];req(d,cols,"data.csv");key(d,"trip_id","data.csv");nums(d,["departure_hour","distance_km","passengers","fare_amount","delay_minutes","is_holiday","revenue","operational_cost"],"data.csv")
    if (d[["distance_km","passengers","fare_amount","delay_minutes","revenue","operational_cost"]]<0).any().any():raise ValueError("negative economics")
    clean=d[cols].sort_values("trip_id");clean.to_csv(out/"trips_clean.csv",index=False)
    rev=clean[["trip_id","revenue","passengers","fare_amount"]].copy();rev["revenue_per_passenger"]=rev.revenue/rev.passengers;rev["fare_revenue_gap"]=rev.revenue-rev.fare_amount*rev.passengers;rev.to_csv(out/"revenue_features.csv",index=False)
    cost=clean[["trip_id","operational_cost","distance_km","delay_minutes"]].copy();cost["cost_per_km"]=cost.operational_cost/cost.distance_km;cost["cost_per_delay_minute"]=np.where(cost.delay_minutes>0,cost.operational_cost/cost.delay_minutes,0);cost.to_csv(out/"cost_features.csv",index=False)
    table=clean.merge(rev.drop(columns=["revenue","passengers","fare_amount"]),on="trip_id",validate="one_to_one").merge(cost.drop(columns=["operational_cost","distance_km","delay_minutes"]),on="trip_id",validate="one_to_one");table["profit"]=table.revenue-table.operational_cost;table["profit_margin"]=table.profit/table.revenue;table.to_csv(out/"trip_economics.csv",index=False)
    features=["departure_hour","distance_km","passengers","fare_amount","delay_minutes","is_holiday","revenue_per_passenger","fare_revenue_gap","cost_per_km","cost_per_delay_minute"];train,test=train_test_split(table,test_size=.2,random_state=42);model=Pipeline([("scale",StandardScaler()),("model",LinearRegression())]);model.fit(train[features],train.profit);pred=model.predict(test[features])
    with (out/"profit_model.pkl").open("wb") as h:pickle.dump(model,h)
    pd.DataFrame({"trip_id":test.trip_id,"actual_profit":test.profit,"predicted_profit":pred}).sort_values("trip_id").to_csv(out/"profit_predictions.csv",index=False);metrics={"train_rows":len(train),"test_rows":len(test),"features":features,"mae":mean_absolute_error(test.profit,pred),"rmse":mean_squared_error(test.profit,pred)**.5,"r2":model.score(test[features],test.profit)};js(out/"profit_metrics.json",metrics)
    routes=table.groupby("route",as_index=False).agg(trip_count=("trip_id","size"),total_revenue=("revenue","sum"),total_cost=("operational_cost","sum"),total_profit=("profit","sum"),mean_profit_margin=("profit_margin","mean")).sort_values("route");routes.to_csv(out/"route_profitability.csv",index=False);js(out/"economics_report.json",{"trips":len(table),"total_revenue":table.revenue.sum(),"total_cost":table.operational_cost.sum(),"total_profit":table.profit.sum(),"model":metrics,"most_profitable_route":routes.sort_values(["total_profit","route"],ascending=[False,True]).iloc[0].route})

RUNNERS={"002_analytics_statistical_integration":experiment,"019_sports_prediction_cleaning_integration":sports_fanout,"023_sports_regression_clustering_visualization":sports_parallel,"063_transportation_clustering_validation":transport_cluster,"079_transportation_regression":economics}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data-dir",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](a.data_dir,a.output_dir)
