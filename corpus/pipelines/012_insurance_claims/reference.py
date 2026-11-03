"""Trusted deterministic references for topology-diverse benchmark batch 04."""
import argparse,json,math,pickle
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.metrics import accuracy_score,f1_score,mean_absolute_error,mean_squared_error,precision_score,recall_score,roc_auc_score,silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def write_json(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda item:item.item() if isinstance(item,np.generic) else str(item))+"\n")
def require(frame,columns,name):
    missing=sorted(set(columns)-set(frame.columns))
    if missing:raise ValueError(f"{name} missing columns {missing}")
    if frame.empty:raise ValueError(f"{name} is empty")
def numeric(frame,columns,name):
    for column in columns:frame[column]=pd.to_numeric(frame[column],errors="coerce")
    if not np.isfinite(frame[columns].to_numpy(float)).all():raise ValueError(f"{name} has non-finite required values")
def unique_nonblank(frame,columns,name):
    if frame.duplicated(columns).any() or any(frame[c].astype(str).str.strip().eq("").any() for c in columns):raise ValueError(f"{name} has invalid key {columns}")


def hr_fanout(data,out):
    d=pd.read_csv(data/"hr_data.csv");cols=["emp_id","department","status","tenure_years","salary","bonus","performance_score","gender","age"]
    require(d,cols,"hr_data.csv");unique_nonblank(d,["emp_id"],"hr_data.csv");numeric(d,cols[3:7]+["age"],"hr_data.csv")
    if (d[["tenure_years","salary","bonus","age"]]<0).any().any() or not d.performance_score.between(1,5).all():raise ValueError("HR measures violate bounds")
    clean=d[cols].sort_values("emp_id").copy();clean["total_compensation"]=clean.salary+clean.bonus;clean.to_csv(out/"workforce_clean.csv",index=False)
    compensation=clean.groupby("department",as_index=False).agg(employee_count=("emp_id","size"),mean_salary=("salary","mean"),median_salary=("salary","median"),total_bonus=("bonus","sum"),mean_total_compensation=("total_compensation","mean")).sort_values("department");compensation.to_csv(out/"compensation_by_department.csv",index=False)
    performance=clean.assign(high_performer=(clean.performance_score>=4).astype(int)).groupby("department",as_index=False).agg(employee_count=("emp_id","size"),mean_performance_score=("performance_score","mean"),high_performer_count=("high_performer","sum"),mean_tenure_years=("tenure_years","mean")).sort_values("department");performance.to_csv(out/"performance_by_department.csv",index=False)
    composition=clean.groupby(["status","gender"],as_index=False).agg(employee_count=("emp_id","size"),mean_age=("age","mean"),mean_tenure_years=("tenure_years","mean")).sort_values(["status","gender"]);composition.to_csv(out/"workforce_composition.csv",index=False)


def claims_fanin(data,out):
    d=pd.read_csv(data/"claims.csv");cols=["claim_id","claim_type","claim_amount","policy_type","incident_date","report_date","report_delay_days","claim_status","is_fraudulent"]
    require(d,cols,"claims.csv");unique_nonblank(d,["claim_id"],"claims.csv");numeric(d,["claim_amount","report_delay_days","is_fraudulent"],"claims.csv")
    if (d[["claim_amount","report_delay_days"]]<0).any().any() or not set(d.is_fraudulent.unique())<={0,1}:raise ValueError("claim values violate bounds")
    d["incident_date"]=pd.to_datetime(d.incident_date,errors="raise");d["report_date"]=pd.to_datetime(d.report_date,errors="raise")
    financial=d.groupby("claim_type",as_index=False).agg(claim_count=("claim_id","size"),total_claim_amount=("claim_amount","sum"),mean_claim_amount=("claim_amount","mean"),median_claim_amount=("claim_amount","median")).sort_values("claim_type");financial.to_csv(out/"financial_by_claim_type.csv",index=False)
    process=d.groupby("claim_status",as_index=False).agg(claim_count=("claim_id","size"),mean_report_delay_days=("report_delay_days","mean"),median_report_delay_days=("report_delay_days","median"),mean_claim_amount=("claim_amount","mean")).sort_values("claim_status");process.to_csv(out/"processing_by_status.csv",index=False)
    fraud=d.groupby("policy_type",as_index=False).agg(claim_count=("claim_id","size"),fraud_count=("is_fraudulent","sum"),fraud_rate=("is_fraudulent","mean"),mean_claim_amount=("claim_amount","mean")).sort_values("policy_type");fraud.to_csv(out/"fraud_by_policy_type.csv",index=False)
    report={"claims":int(financial.claim_count.sum()),"total_claim_amount":financial.total_claim_amount.sum(),"fraudulent_claims":int(fraud.fraud_count.sum()),"highest_amount_claim_type":financial.sort_values(["total_claim_amount","claim_type"],ascending=[False,True]).iloc[0].claim_type,"slowest_claim_status":process.sort_values(["mean_report_delay_days","claim_status"],ascending=[False,True]).iloc[0].claim_status,"highest_fraud_rate_policy_type":fraud.sort_values(["fraud_rate","policy_type"],ascending=[False,True]).iloc[0].policy_type};write_json(out/"claims_report.json",report)


def _classification(train,test,features,target,prefix,out):
    model=Pipeline([("scale",StandardScaler()),("model",LogisticRegression(C=1.0,solver="liblinear",max_iter=1000,random_state=42))]);model.fit(train[features],train[target]);prob=model.predict_proba(test[features])[:,1];pred=(prob>=.5).astype(int)
    with (out/f"{prefix}_model.pkl").open("wb") as h:pickle.dump(model,h)
    predictions=pd.DataFrame({"machine_id":test.machine_id,"timestamp":test.timestamp,"actual":test[target],"probability":prob,"predicted":pred});predictions.to_csv(out/f"{prefix}_predictions.csv",index=False)
    result={"target":target,"train_rows":len(train),"test_rows":len(test),"features":features,"accuracy":accuracy_score(test[target],pred),"precision":precision_score(test[target],pred,zero_division=0),"recall":recall_score(test[target],pred,zero_division=0),"f1":f1_score(test[target],pred,zero_division=0),"roc_auc":roc_auc_score(test[target],prob)};write_json(out/f"{prefix}_metrics.json",result);return result


def maintenance(data,out):
    d=pd.read_csv(data/"sensor_readings.csv");sensors=["temperature_c","vibration_mm_s","pressure_bar","rpm","power_consumption_kw","noise_db","humidity_pct"];targets=["is_failure","failure_within_24h","failure_within_7d"];cols=["machine_id","machine_type","timestamp",*sensors,*targets]
    require(d,cols,"sensor_readings.csv");unique_nonblank(d,["machine_id","timestamp"],"sensor_readings.csv");numeric(d,sensors+targets,"sensor_readings.csv")
    if any(not set(d[t].unique())<={0,1} for t in targets):raise ValueError("maintenance targets must be binary")
    d["timestamp"]=pd.to_datetime(d.timestamp,errors="raise");clean=d[cols].sort_values(["machine_id","timestamp"]).reset_index(drop=True)
    for _,group in clean.groupby("machine_id"):
        if not group.timestamp.diff().dropna().eq(pd.Timedelta(hours=1)).all():raise ValueError("machine series must be hourly and continuous")
    clean.to_csv(out/"sensor_clean.csv",index=False,date_format="%Y-%m-%d %H:%M:%S")
    temporal=clean[["machine_id","timestamp"]].copy()
    for column in ["temperature_c","vibration_mm_s","power_consumption_kw"]:
        grouped=clean.groupby("machine_id")[column];temporal[f"{column}_lag1"]=grouped.shift(1);temporal[f"{column}_rolling24_mean"]=grouped.transform(lambda s:s.shift(1).rolling(24,min_periods=24).mean())
    temporal.to_csv(out/"temporal_features.csv",index=False,date_format="%Y-%m-%d %H:%M:%S")
    baseline=clean[["machine_id","timestamp"]].copy()
    for column in ["temperature_c","vibration_mm_s"]:
        grouped=clean.groupby("machine_id")[column];baseline[f"{column}_prior_mean"]=grouped.transform(lambda s:s.shift(1).expanding(min_periods=24).mean());baseline[f"{column}_prior_std"]=grouped.transform(lambda s:s.shift(1).expanding(min_periods=24).std(ddof=0))
    baseline.to_csv(out/"expanding_baselines.csv",index=False,date_format="%Y-%m-%d %H:%M:%S")
    integrated=clean.merge(temporal,on=["machine_id","timestamp"],validate="one_to_one").merge(baseline,on=["machine_id","timestamp"],validate="one_to_one").dropna().sort_values(["timestamp","machine_id"]).reset_index(drop=True);integrated.to_csv(out/"maintenance_features.csv",index=False,date_format="%Y-%m-%d %H:%M:%S")
    features=[*sensors,*[c for c in temporal.columns if c not in {"machine_id","timestamp"}],*[c for c in baseline.columns if c not in {"machine_id","timestamp"}]]
    cut=math.floor(.8*len(integrated));train=integrated.iloc[:cut];test=integrated.iloc[cut:]
    m24=_classification(train,test,features,"failure_within_24h","failure24h",out);m7=_classification(train,test,features,"failure_within_7d","failure7d",out)
    risk=integrated.groupby("machine_id",as_index=False).agg(observations=("timestamp","size"),failure_count=("is_failure","sum"),failure24h_rate=("failure_within_24h","mean"),failure7d_rate=("failure_within_7d","mean"),mean_temperature_c=("temperature_c","mean"),mean_vibration_mm_s=("vibration_mm_s","mean")).sort_values("machine_id");risk.to_csv(out/"machine_risk_summary.csv",index=False)
    write_json(out/"maintenance_report.json",{"rows":len(integrated),"machines":len(risk),"failure24h_model":m24,"failure7d_model":m7,"highest_failure7d_machine":risk.sort_values(["failure7d_rate","machine_id"],ascending=[False,True]).iloc[0].machine_id})


def sports_parallel(data,out):
    d=pd.read_csv(data/"data.csv");cluster_features=["points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","play_style_score","efficiency_rating","usage_rate"];prediction_features=["games_played","points_per_game","assists_per_game","rebounds_per_game","minutes_per_game","age","experience_years","salary_millions","efficiency_rating","usage_rate","injury_games_missed","field_goal_pct","three_point_pct","free_throw_pct"]
    require(d,["player_id","team","position","all_star",*set(cluster_features+prediction_features)],"data.csv");unique_nonblank(d,["player_id"],"data.csv");numeric(d,[*set(cluster_features+prediction_features),"all_star"],"data.csv")
    if not set(d.all_star.unique())<={0,1}:raise ValueError("all_star must be binary")
    cluster_data=d[["player_id","team","position",*cluster_features]].sort_values("player_id");cluster_data.to_csv(out/"clustering_features.csv",index=False)
    scaler=StandardScaler();x=scaler.fit_transform(cluster_data[cluster_features]);model=KMeans(n_clusters=4,random_state=42,n_init=20,algorithm="lloyd").fit(x)
    order=np.lexsort((np.arange(4),model.cluster_centers_[:,cluster_features.index("usage_rate")],model.cluster_centers_[:,cluster_features.index("efficiency_rating")]));mapping={int(raw):int(label) for label,raw in enumerate(order)}
    assigned=cluster_data.copy();assigned["cluster"]=[mapping[int(v)] for v in model.labels_];assigned.to_csv(out/"player_clusters.csv",index=False)
    with (out/"cluster_model.pkl").open("wb") as h:pickle.dump({"scaler":scaler,"model":model,"mapping":mapping,"features":cluster_features},h)
    profile=assigned.groupby("cluster",as_index=False).agg(player_count=("player_id","size"),mean_points=("points_per_game","mean"),mean_assists=("assists_per_game","mean"),mean_rebounds=("rebounds_per_game","mean"),mean_efficiency=("efficiency_rating","mean"),mean_usage=("usage_rate","mean")).sort_values("cluster");profile.to_csv(out/"cluster_profiles.csv",index=False);write_json(out/"cluster_report.json",{"players":len(assigned),"clusters":4,"silhouette_score":silhouette_score(x,model.labels_)})
    prediction=d[["player_id","all_star",*prediction_features]].sort_values("player_id");prediction.to_csv(out/"prediction_features.csv",index=False)
    train,test=train_test_split(prediction,test_size=.25,random_state=42,stratify=prediction.all_star);model2=Pipeline([("scale",StandardScaler()),("model",LogisticRegression(C=1.0,solver="liblinear",max_iter=1000,random_state=42))]);model2.fit(train[prediction_features],train.all_star);prob=model2.predict_proba(test[prediction_features])[:,1];pred=(prob>=.5).astype(int)
    with (out/"all_star_model.pkl").open("wb") as h:pickle.dump(model2,h)
    predictions=pd.DataFrame({"player_id":test.player_id,"actual_all_star":test.all_star,"probability":prob,"predicted_all_star":pred}).sort_values("player_id");predictions.to_csv(out/"all_star_predictions.csv",index=False)
    metrics={"train_rows":len(train),"test_rows":len(test),"features":prediction_features,"accuracy":accuracy_score(test.all_star,pred),"precision":precision_score(test.all_star,pred,zero_division=0),"recall":recall_score(test.all_star,pred,zero_division=0),"f1":f1_score(test.all_star,pred,zero_division=0),"roc_auc":roc_auc_score(test.all_star,prob)};write_json(out/"all_star_metrics.json",metrics)


def transportation(data,out):
    d=pd.read_csv(data/"data.csv");cols=["trip_id","route","vehicle_type","departure_hour","distance_km","passengers","fare_amount","delay_minutes","day_of_week","is_holiday","weather_condition"]
    require(d,cols,"data.csv");unique_nonblank(d,["trip_id"],"data.csv");numeric(d,["departure_hour","distance_km","passengers","fare_amount","delay_minutes","is_holiday"],"data.csv")
    if not d.departure_hour.between(0,23).all() or (d[["distance_km","passengers","fare_amount","delay_minutes"]]<0).any().any() or not set(d.is_holiday.unique())<={0,1}:raise ValueError("trip values violate bounds")
    clean=d[cols].sort_values("trip_id");clean.to_csv(out/"trips_clean.csv",index=False)
    features=clean.copy();features["fare_per_passenger"]=np.where(features.passengers>0,features.fare_amount/features.passengers,0);features["distance_holiday_interaction"]=features.distance_km*features.is_holiday;features.to_csv(out/"trip_features.csv",index=False)
    predictors=["departure_hour","distance_km","passengers","fare_amount","is_holiday","fare_per_passenger","distance_holiday_interaction"]
    train,test=train_test_split(features,test_size=.2,random_state=42);train=train.sort_values("trip_id");test=test.sort_values("trip_id");train.to_csv(out/"train.csv",index=False);test.to_csv(out/"test.csv",index=False)
    model=Pipeline([("scale",StandardScaler()),("model",Ridge(alpha=1.0,solver="svd"))]);model.fit(train[predictors],train.delay_minutes);pred=model.predict(test[predictors])
    with (out/"model.pkl").open("wb") as h:pickle.dump(model,h)
    predictions=pd.DataFrame({"trip_id":test.trip_id,"actual_delay_minutes":test.delay_minutes,"predicted_delay_minutes":pred});predictions.to_csv(out/"predictions.csv",index=False)
    metrics={"train_rows":len(train),"test_rows":len(test),"features":predictors,"mae_minutes":mean_absolute_error(test.delay_minutes,pred),"rmse_minutes":mean_squared_error(test.delay_minutes,pred)**.5};write_json(out/"metrics.json",metrics);write_json(out/"delay_report.json",metrics)


RUNNERS={"011_hr_visualization_integration_validation":hr_fanout,"012_insurance_claims":claims_fanin,"013_predictive_maintenance":maintenance,"015_sports_clustering_prediction_statistical":sports_parallel,"055_transportation_analysis":transportation}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data-dir",type=Path,required=True);p.add_argument("--output-dir",type=Path,required=True);a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](a.data_dir,a.output_dir)
