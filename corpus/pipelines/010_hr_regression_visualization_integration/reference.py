"""Trusted deterministic references for benchmark batch 03."""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def require(frame, columns, name):
    missing=sorted(set(columns)-set(frame.columns))
    if missing: raise ValueError(f"{name} missing columns: {missing}")
    if frame.empty: raise ValueError(f"{name} is empty")


def numeric(frame, columns, name):
    for column in columns: frame[column]=pd.to_numeric(frame[column],errors="coerce")
    if not np.isfinite(frame[columns].to_numpy(float)).all(): raise ValueError(f"{name} has missing/non-finite numeric values")


def nonblank_unique(frame, columns, name):
    for column in columns:
        if frame[column].astype(str).str.strip().eq("").any() or frame.duplicated(columns).any():
            raise ValueError(f"{name} has blank or duplicate key {columns}")


def finance(data, out):
    stocks=pd.read_csv(data/"stocks.csv"); market=pd.read_csv(data/"market_indices.csv")
    sc=["ticker","sector","date","open","high","low","close","volume"];mc=["date","sp500","nasdaq"]
    require(stocks,sc,"stocks.csv");require(market,mc,"market_indices.csv")
    nonblank_unique(stocks,["ticker","date"],"stocks.csv");nonblank_unique(market,["date"],"market_indices.csv")
    numeric(stocks,["open","high","low","close","volume"],"stocks.csv");numeric(market,["sp500","nasdaq"],"market_indices.csv")
    stocks["date"]=pd.to_datetime(stocks.date,errors="raise");market["date"]=pd.to_datetime(market.date,errors="raise")
    if (stocks[["open","high","low","close","volume"]]<0).any().any() or (market[["sp500","nasdaq"]]<=0).any().any(): raise ValueError("prices, volume, and index levels violate bounds")
    stocks["high"]=stocks[["open","high","low","close"]].max(axis=1)
    stocks["low"]=stocks[["open","high","low","close"]].min(axis=1)
    clean_stocks=stocks[sc].sort_values(["ticker","date"]);clean_market=market[mc].sort_values("date")
    clean_stocks.to_csv(out/"clean_stocks.csv",index=False,date_format="%Y-%m-%d");clean_market.to_csv(out/"clean_market.csv",index=False,date_format="%Y-%m-%d")
    write_json(out/"stock_quality.json",{"rows":len(clean_stocks),"tickers":clean_stocks.ticker.nunique(),"dates":clean_stocks.date.nunique()})
    write_json(out/"market_quality.json",{"rows":len(clean_market),"dates":clean_market.date.nunique()})
    stock=clean_stocks.copy();stock["stock_return"]=stock.groupby("ticker").close.pct_change()
    idx=clean_market.copy();idx["sp500_return"]=idx.sp500.pct_change();idx["nasdaq_return"]=idx.nasdaq.pct_change()
    panel=stock.merge(idx,on="date",how="inner",validate="many_to_one")
    panel["excess_sp500_return"]=panel.stock_return-panel.sp500_return
    panel=panel.sort_values(["ticker","date"]);panel.to_csv(out/"market_panel.csv",index=False,date_format="%Y-%m-%d")
    write_json(out/"integration.json",{"stock_rows":len(stock),"panel_rows":len(panel),"matched_dates":panel.date.nunique(),"unmatched_stock_rows":len(stock)-len(panel)})
    eligible=panel.dropna(subset=["stock_return","sp500_return","nasdaq_return"])
    stats=eligible.groupby(["ticker","sector"],as_index=False).agg(observations=("stock_return","size"),mean_return=("stock_return","mean"),volatility=("stock_return",lambda s:s.std(ddof=1)),mean_excess_sp500_return=("excess_sp500_return","mean"))
    correlations=[]
    for ticker,group in eligible.groupby("ticker"):
        correlations.append([ticker,group.stock_return.corr(group.sp500_return),group.stock_return.corr(group.nasdaq_return)])
    relationships=pd.DataFrame(correlations,columns=["ticker","sp500_correlation","nasdaq_correlation"]).sort_values("ticker")
    stats=stats.sort_values("ticker");stats.to_csv(out/"ticker_statistics.csv",index=False);relationships.to_csv(out/"market_relationships.csv",index=False)
    report={"rows":len(panel),"eligible_return_rows":len(eligible),"tickers":stats.ticker.nunique(),"matched_dates":panel.date.nunique(),"highest_volatility_ticker":stats.sort_values(["volatility","ticker"],ascending=[False,True]).iloc[0].ticker,"highest_sp500_correlation_ticker":relationships.sort_values(["sp500_correlation","ticker"],ascending=[False,True]).iloc[0].ticker}
    write_json(out/"finance_report.json",report)


def attrition_parallel(data, out):
    employees=pd.read_csv(data/"employees.csv");engagement=pd.read_csv(data/"engagement_surveys.csv");performance=pd.read_csv(data/"performance_reviews.csv")
    ec=["employee_id","department","monthly_salary","overtime","job_satisfaction","is_attrited"]
    gc=["employee_id","survey_date","engagement_score","satisfaction_score","manager_score","career_growth_score","work_env_score"]
    pc=["employee_id","review_year","performance_score","goal_achievement_pct","peer_feedback_score","manager_rating","promotion_recommended"]
    require(employees,ec,"employees.csv");require(engagement,gc,"engagement_surveys.csv");require(performance,pc,"performance_reviews.csv")
    nonblank_unique(employees,["employee_id"],"employees.csv")
    numeric(employees,["monthly_salary","job_satisfaction","is_attrited"],"employees.csv")
    if not set(employees.is_attrited.unique())<={0,1}:raise ValueError("is_attrited must be binary")
    workforce=employees[ec].sort_values("employee_id");workforce.to_csv(out/"workforce.csv",index=False)
    by_department=workforce.groupby("department",as_index=False).agg(employee_count=("employee_id","size"),attrition_count=("is_attrited","sum"),attrition_rate=("is_attrited","mean"),mean_salary=("monthly_salary","mean"),mean_job_satisfaction=("job_satisfaction","mean")).sort_values("department")
    by_department.to_csv(out/"attrition_by_department.csv",index=False)
    write_json(out/"attrition_report.json",{"employees":len(workforce),"attrited":int(workforce.is_attrited.sum()),"attrition_rate":workforce.is_attrited.mean(),"departments":len(by_department)})
    if not set(engagement.employee_id)<=set(employees.employee_id):raise ValueError("unknown engagement employee")
    numeric(engagement,gc[2:],"engagement_surveys.csv");engagement["survey_date"]=pd.to_datetime(engagement.survey_date,errors="raise")
    engagement["engagement_composite"]=engagement[gc[2:]].mean(axis=1)
    engagement_employee=engagement.groupby("employee_id",as_index=False).agg(survey_count=("survey_date","size"),mean_engagement_composite=("engagement_composite","mean"),latest_survey_date=("survey_date","max")).sort_values("employee_id")
    engagement_employee.latest_survey_date=engagement_employee.latest_survey_date.dt.strftime("%Y-%m-%d");engagement_employee.to_csv(out/"engagement_by_employee.csv",index=False)
    engagement["month"]=engagement.survey_date.dt.to_period("M").astype(str)
    monthly=engagement.groupby("month",as_index=False).agg(survey_count=("employee_id","size"),mean_engagement_composite=("engagement_composite","mean")).sort_values("month")
    monthly.to_csv(out/"engagement_by_month.csv",index=False)
    write_json(out/"engagement_report.json",{"survey_rows":len(engagement),"surveyed_employees":engagement.employee_id.nunique(),"months":len(monthly),"overall_mean_composite":engagement.engagement_composite.mean()})
    if not set(performance.employee_id)<=set(employees.employee_id):raise ValueError("unknown performance employee")
    numeric(performance,pc[1:],"performance_reviews.csv")
    performance_employee=performance.groupby("employee_id",as_index=False).agg(review_count=("review_year","size"),mean_performance_score=("performance_score","mean"),mean_goal_achievement_pct=("goal_achievement_pct","mean"),promotion_recommendations=("promotion_recommended","sum")).sort_values("employee_id")
    performance_employee.to_csv(out/"performance_by_employee.csv",index=False)
    perf_join=performance_employee.merge(employees[["employee_id","department"]],on="employee_id",validate="one_to_one")
    perf_department=perf_join.groupby("department",as_index=False).agg(reviewed_employees=("employee_id","size"),mean_performance_score=("mean_performance_score","mean"),mean_goal_achievement_pct=("mean_goal_achievement_pct","mean"),promotion_recommendations=("promotion_recommendations","sum")).sort_values("department")
    perf_department.to_csv(out/"performance_by_department.csv",index=False)
    write_json(out/"performance_report.json",{"review_rows":len(performance),"reviewed_employees":performance.employee_id.nunique(),"departments":len(perf_department),"mean_performance_score":performance.performance_score.mean()})


def healthcare(data, out):
    patients=pd.read_csv(data/"patients.csv");admissions=pd.read_csv(data/"admissions.csv");labs=pd.read_csv(data/"lab_results.csv");meds=pd.read_csv(data/"medications.csv")
    pc=["patient_id","age","gender","race","conditions","has_diabetes","has_heart_condition","bmi","smoker","insurance_type","n_conditions","readmitted_30d"]
    ac=["admission_id","patient_id","length_of_stay","icu_stay","n_procedures","er_admission"]
    lc=["admission_id","patient_id","test_name","test_value","abnormal_flag"]
    mc=["admission_id","patient_id","medication"]
    require(patients,pc,"patients.csv");require(admissions,ac,"admissions.csv");require(labs,lc,"lab_results.csv");require(meds,mc,"medications.csv")
    nonblank_unique(patients,["patient_id"],"patients.csv");nonblank_unique(admissions,["admission_id"],"admissions.csv")
    for frame,name in [(admissions,"admissions"),(labs,"labs"),(meds,"medications")]:
        if not set(frame.patient_id)<=set(patients.patient_id):raise ValueError(f"unknown {name} patient")
    if not set(labs.admission_id)<=set(admissions.admission_id) or not set(meds.admission_id)<=set(admissions.admission_id):raise ValueError("unknown lab/medication admission")
    numeric(patients,["age","has_diabetes","has_heart_condition","bmi","smoker","n_conditions","readmitted_30d"],"patients.csv")
    numeric(admissions,ac[2:],"admissions.csv");numeric(labs,["test_value","abnormal_flag"],"lab_results.csv")
    if not set(patients.readmitted_30d.unique())<={0,1}:raise ValueError("readmitted_30d must be binary")
    clean=patients[pc].sort_values("patient_id");clean.to_csv(out/"patients_clean.csv",index=False)
    adm=admissions.groupby("patient_id",as_index=False).agg(admission_count=("admission_id","size"),total_length_of_stay=("length_of_stay","sum"),mean_length_of_stay=("length_of_stay","mean"),icu_admission_count=("icu_stay","sum"),total_procedures=("n_procedures","sum"),er_admission_count=("er_admission","sum")).sort_values("patient_id");adm.to_csv(out/"admissions_by_patient.csv",index=False)
    lab=labs.groupby("patient_id",as_index=False).agg(lab_count=("test_name","size"),abnormal_lab_count=("abnormal_flag","sum"),mean_test_value=("test_value","mean")).sort_values("patient_id");lab.to_csv(out/"labs_by_patient.csv",index=False)
    med=meds.groupby("patient_id",as_index=False).agg(medication_record_count=("medication","size"),unique_medications=("medication","nunique")).sort_values("patient_id");med.to_csv(out/"medications_by_patient.csv",index=False)
    features=clean.merge(adm,on="patient_id",how="left",validate="one_to_one").merge(lab,on="patient_id",how="left",validate="one_to_one").merge(med,on="patient_id",how="left",validate="one_to_one")
    derived=[*adm.columns[1:],*lab.columns[1:],*med.columns[1:]];features[derived]=features[derived].fillna(0);features=features.sort_values("patient_id");features.to_csv(out/"patient_features.csv",index=False)
    model_features=["age","has_diabetes","has_heart_condition","bmi","smoker","n_conditions",*derived]
    train,test=train_test_split(features,test_size=.25,random_state=42,stratify=features.readmitted_30d)
    model=Pipeline([("scale",StandardScaler()),("model",LogisticRegression(C=1.0,solver="liblinear",max_iter=1000,random_state=42))]);model.fit(train[model_features],train.readmitted_30d)
    prob=model.predict_proba(test[model_features])[:,1];pred=(prob>=.5).astype(int)
    predictions=pd.DataFrame({"patient_id":test.patient_id,"actual_readmitted":test.readmitted_30d,"readmission_probability":prob,"predicted_readmitted":pred}).sort_values("patient_id");predictions.to_csv(out/"predictions.csv",index=False)
    with (out/"model.pkl").open("wb") as h:pickle.dump(model,h)
    metrics={"train_rows":len(train),"test_rows":len(test),"features":model_features,"accuracy":accuracy_score(test.readmitted_30d,pred),"precision":precision_score(test.readmitted_30d,pred,zero_division=0),"recall":recall_score(test.readmitted_30d,pred,zero_division=0),"f1":f1_score(test.readmitted_30d,pred,zero_division=0),"roc_auc":roc_auc_score(test.readmitted_30d,prob)};write_json(out/"readmission_metrics.json",metrics)
    utilization=features.groupby("readmitted_30d",as_index=False).agg(patient_count=("patient_id","size"),mean_admission_count=("admission_count","mean"),mean_total_length_of_stay=("total_length_of_stay","mean"),mean_er_admission_count=("er_admission_count","mean")).sort_values("readmitted_30d");utilization.to_csv(out/"utilization_by_readmission.csv",index=False)
    clinical=features.groupby("insurance_type",as_index=False).agg(patient_count=("patient_id","size"),readmission_rate=("readmitted_30d","mean"),mean_abnormal_lab_count=("abnormal_lab_count","mean"),mean_unique_medications=("unique_medications","mean")).sort_values("insurance_type");clinical.to_csv(out/"clinical_summary.csv",index=False)
    report={"patients":len(features),"admissions":len(admissions),"labs":len(labs),"medication_records":len(meds),"model":metrics,"readmission_groups":len(utilization),"insurance_groups":len(clinical)};write_json(out/"readmission_report.json",report)


def hr_fanout(data, out):
    employees=pd.read_csv(data/"employees.csv");departments=pd.read_csv(data/"departments.csv")
    ec=["emp_id","department","role","experience_years","education","performance_score","age","gender","salary"];dc=["department","headcount","budget_millions","location"]
    require(employees,ec,"employees.csv");require(departments,dc,"departments.csv");nonblank_unique(employees,["emp_id"],"employees.csv");nonblank_unique(departments,["department"],"departments.csv")
    if not set(employees.department)<=set(departments.department):raise ValueError("unknown employee department")
    numeric(employees,["experience_years","performance_score","age","salary"],"employees.csv");numeric(departments,["headcount","budget_millions"],"departments.csv")
    workforce=employees[ec].merge(departments[dc],on="department",validate="many_to_one").sort_values("emp_id");workforce.to_csv(out/"workforce.csv",index=False)
    features=workforce.copy();features["salary_per_experience_year"]=features.salary/(features.experience_years+1);features["budget_per_head_millions"]=features.budget_millions/features.headcount;features.to_csv(out/"workforce_features.csv",index=False)
    model_features=["experience_years","performance_score","age","headcount","budget_millions"]
    train,test=train_test_split(features,test_size=.2,random_state=42)
    model=LinearRegression().fit(train[model_features],train.salary);pred=model.predict(test[model_features])
    predictions=pd.DataFrame({"emp_id":test.emp_id,"actual_salary":test.salary,"predicted_salary":pred}).sort_values("emp_id");predictions.to_csv(out/"salary_predictions.csv",index=False)
    with (out/"salary_model.pkl").open("wb") as h:pickle.dump(model,h)
    write_json(out/"salary_metrics.json",{"train_rows":len(train),"test_rows":len(test),"features":model_features,"mae":mean_absolute_error(test.salary,pred),"rmse":mean_squared_error(test.salary,pred)**.5,"r2":model.score(test[model_features],test.salary)})
    department=features.groupby("department",as_index=False).agg(employee_rows=("emp_id","size"),declared_headcount=("headcount","first"),budget_millions=("budget_millions","first"),mean_salary=("salary","mean"),mean_performance_score=("performance_score","mean")).sort_values("department");department.to_csv(out/"department_summary.csv",index=False)
    gender=features.groupby("gender",as_index=False).agg(employee_count=("emp_id","size"),mean_salary=("salary","mean"),median_salary=("salary","median"),mean_experience_years=("experience_years","mean")).sort_values("gender");gender.to_csv(out/"gender_pay_summary.csv",index=False)


def students(data, out):
    frame=pd.read_csv(data/"data.csv");columns=["student_id","major","year","age","study_hours_per_week","attendance_pct","previous_gpa","current_gpa","assignments_completed","extracurricular_hours"]
    require(frame,columns,"data.csv");nonblank_unique(frame,["student_id"],"data.csv");numeric(frame,columns[2:],"data.csv")
    if not frame.attendance_pct.between(0,100).all() or not frame[["previous_gpa","current_gpa"]].apply(lambda s:s.between(0,4)).all().all():raise ValueError("attendance/GPA out of range")
    clean=frame[columns].sort_values("student_id");clean.to_csv(out/"students_clean.csv",index=False)
    features=clean.copy();features["study_attendance_interaction"]=features.study_hours_per_week*features.attendance_pct/100;features["gpa_change"]=features.current_gpa-features.previous_gpa;features.to_csv(out/"student_features.csv",index=False)
    predictors=["year","age","study_hours_per_week","attendance_pct","previous_gpa","assignments_completed","extracurricular_hours","study_attendance_interaction"]
    train,test=train_test_split(features,test_size=.2,random_state=42);train=train.sort_values("student_id");test=test.sort_values("student_id");train.to_csv(out/"train.csv",index=False);test.to_csv(out/"test.csv",index=False)
    model=Pipeline([("scale",StandardScaler()),("model",Ridge(alpha=1.0,solver="svd"))]);model.fit(train[predictors],train.current_gpa);pred=model.predict(test[predictors])
    with (out/"model.pkl").open("wb") as h:pickle.dump(model,h)
    predictions=pd.DataFrame({"student_id":test.student_id,"actual_gpa":test.current_gpa,"predicted_gpa":pred});predictions.to_csv(out/"predictions.csv",index=False)
    metrics={"train_rows":len(train),"test_rows":len(test),"features":predictors,"mae":mean_absolute_error(test.current_gpa,pred),"rmse":mean_squared_error(test.current_gpa,pred)**.5};write_json(out/"metrics.json",metrics);write_json(out/"student_report.json",metrics)


RUNNERS={"001_analytics_statistical_cleaning_integration":finance,"007_employee_attrition":attrition_parallel,"009_healthcare_readmission":healthcare,"010_hr_regression_visualization_integration":hr_fanout,"054_student_performance":students}


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--data-dir",type=Path,required=True);parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](args.data_dir,args.output_dir)
