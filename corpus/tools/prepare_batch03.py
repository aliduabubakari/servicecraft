"""Materialize the five topology-diverse batch-03 benchmark cases."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT.parent/"custom-pipelines"
REV=subprocess.check_output(["git","-C",str(UPSTREAM),"rev-parse","HEAD"],text=True).strip()


def task(identifier,name,operation,inputs,outputs,requirements,parameters=None):
    return {"id":identifier,"name":name,"operation":operation,"required":True,"inputs":inputs,"outputs":outputs,"requirements":requirements,"parameters":parameters or {}}


def artifact(name,columns=None):
    return {"id":name,"path":name,"format":Path(name).suffix[1:],"required_columns":columns or []}


COMMON="""

Execution contract: generate executable local Dagster code. Do not use networks, external services, prior-run outputs, fixed analytical answers, or human intervention. The required topology is semantically necessary: independent branches must not consume one another's outputs, while every declared join must consume the listed branch artifacts. A different Dagster asset/op decomposition is allowed only if it preserves the logical tasks, data dependencies, topology class, and observable checkpoints. Write outputs beneath the run output directory. Preserve full numeric precision; comparisons use atol=1e-6 and rtol=1e-6. JSON must be finite. Missing columns, invalid primary/foreign keys, invalid dates, or non-finite required values must fail clearly.

Mandatory output files:
"""


CASES={
"001_analytics_statistical_cleaning_integration":{
"title":"Stock and market return integration with convergent validation","domain":"finance","family":"multisource_market_integration","topology":"linear_to_fan_in","runner":"finance",
"reason":"Two sources naturally support independent validation before a keyed join; the upstream prose does not make that convergence observable.",
"sources":{"stocks.csv":("stocks.csv","csv"),"market_indices.csv":("market_indices.csv","csv")},
"columns":{"stocks.csv":["ticker","sector","date","open","high","low","close","volume"],"market_indices.csv":["date","sp500","nasdaq"]},
"description":"""Build a stock/market analysis pipeline with two independent source-validation branches that converge, followed by a linear analysis and report suffix. This required `linear_to_fan_in` topology is justified because stock and index validity can be established independently, but return comparisons require both sources.

The stock branch validates unique (ticker,date), nonblank ticker/sector, parseable dates, and nonnegative finite OHLC/volume. The synthetic source contains recoverable OHLC inconsistencies: normalize high to the maximum and low to the minimum of the row's original open/high/low/close values. It emits clean_stocks.csv sorted ticker/date and stock_quality.json. The market branch independently validates unique dates, positive finite S&P 500 and Nasdaq levels, and emits clean_market.csv sorted by date plus market_quality.json.

The join task computes within-ticker close-to-close stock_return and daily sp500_return/nasdaq_return before an inner many-to-one date join. It computes excess_sp500_return and emits market_panel.csv plus integration.json with source/panel counts, matched dates, and unmatched stock rows. First observations per return series remain missing; do not replace them.

Using rows with all three returns present, calculate ticker_statistics.csv with observations, mean_return, sample volatility (ddof=1), and mean_excess_sp500_return. market_relationships.csv contains Pearson stock-return correlations with each index. Sort both by ticker. finance_report.json publishes panel/eligible counts, tickers, matched dates, and the highest-volatility and highest-S&P-correlation tickers, breaking ties by ticker ascending.""",
"artifacts":[artifact("clean_stocks.csv",["ticker","sector","date","close"]),artifact("stock_quality.json"),artifact("clean_market.csv",["date","sp500","nasdaq"]),artifact("market_quality.json"),artifact("market_panel.csv",["ticker","date","stock_return","sp500_return","nasdaq_return","excess_sp500_return"]),artifact("integration.json"),artifact("ticker_statistics.csv",["ticker","sector","observations","mean_return","volatility","mean_excess_sp500_return"]),artifact("market_relationships.csv",["ticker","sp500_correlation","nasdaq_correlation"]),artifact("finance_report.json")],
"tasks":[
task("validate_stocks","Validate and normalize the stock branch","source_validation_cleaning",["input:stocks.csv"],["clean_stocks.csv","stock_quality.json"],["Validate stock keys, dates, finite values, and nonnegative bounds; normalize high/low using row extrema."]),
task("validate_market","Validate the market-index branch","source_validation",["input:market_indices.csv"],["clean_market.csv","market_quality.json"],["Validate index dates, levels, and uniqueness independently of stocks."]),
task("integrate","Join return-enriched stock and market branches","temporal_join",["clean_stocks.csv","stock_quality.json","clean_market.csv","market_quality.json"],["market_panel.csv","integration.json"],["Compute returns before an inner date join and retain first-return missing values.","Publish join reconciliation counts."],{"join":"inner","cardinality":"many_to_one"}),
task("analyze","Compute ticker statistics and index relationships","statistical_analysis",["market_panel.csv","integration.json"],["ticker_statistics.csv","market_relationships.csv"],["Use complete-return rows, sample volatility, and Pearson correlation."]),
task("report","Publish the integrated market report","aggregate_report",["ticker_statistics.csv","market_relationships.csv"],["finance_report.json"],["Publish derived counts and deterministically ranked tickers."])]},

"007_employee_attrition":{
"title":"Independent workforce, engagement, and performance analytics","domain":"human_resources","family":"parallel_workforce_analytics","topology":"parallel","runner":"attrition_parallel",
"reason":"The three source-specific descriptive analyses can execute independently; joining them would add an artificial dependency and discard employees without surveys.",
"sources":{"employees.csv":("employees.csv","csv"),"engagement_surveys.csv":("engagement_surveys.json","json"),"performance_reviews.csv":("performance_reviews.xlsx","xlsx")},
"columns":{"employees.csv":["employee_id","department","monthly_salary","overtime","job_satisfaction","is_attrited"],"engagement_surveys.csv":["employee_id","survey_date","engagement_score","satisfaction_score","manager_score","career_growth_score","work_env_score"],"performance_reviews.csv":["employee_id","review_year","performance_score","goal_achievement_pct","peer_feedback_score","manager_rating","promotion_recommended"]},
"description":"""Build three independent two-task analytics branches. The required `parallel` topology has no artifact dependency between branches: workforce attrition uses employees.csv, engagement trends use engagement_surveys.csv, and performance summaries use performance_reviews.csv. Employee IDs in the latter sources must be members of employees.csv, but that source is a validation lookup rather than an output dependency. Do not merge the three analytical tables.

Workforce branch: validate unique nonblank employee_id and binary is_attrited, retain the six named columns in workforce.csv sorted by employee_id, then group by department into employee_count, attrition_count, attrition_rate, mean_salary, and mean_job_satisfaction. attrition_report.json gives total employees, attrited employees, overall rate, and department count.

Engagement branch: parse dates and validate the five finite score fields. Compute engagement_composite as their row mean. Aggregate by employee into survey_count, mean_engagement_composite, latest_survey_date; separately group by YYYY-MM into survey_count and mean composite. engagement_report.json gives survey rows, surveyed employees, months, and overall mean composite.

Performance branch: validate finite review measures. Aggregate by employee into review_count, mean performance, mean goal achievement, and count/sum of promotion recommendations. Use employees.csv only to attach department, then summarize reviewed employees, performance, goal achievement, and recommendations by department. performance_report.json gives review rows, reviewed employees, department count, and overall mean performance.

All branch outputs are mandatory. Parallelism is part of RQ1: connecting one branch after another, or combining them through a synthetic final report, is dependency-incorrect.""",
"artifacts":[artifact("workforce.csv",["employee_id","department","is_attrited"]),artifact("attrition_by_department.csv",["department","employee_count","attrition_count","attrition_rate"]),artifact("attrition_report.json"),artifact("engagement_by_employee.csv",["employee_id","survey_count","mean_engagement_composite","latest_survey_date"]),artifact("engagement_by_month.csv",["month","survey_count","mean_engagement_composite"]),artifact("engagement_report.json"),artifact("performance_by_employee.csv",["employee_id","review_count","mean_performance_score"]),artifact("performance_by_department.csv",["department","reviewed_employees","mean_performance_score"]),artifact("performance_report.json")],
"tasks":[
task("prepare_workforce","Validate workforce records","source_validation",["input:employees.csv"],["workforce.csv"],["Validate employee keys, target flag, and required measures."]),
task("summarize_attrition","Summarize attrition by department","grouped_aggregation",["workforce.csv"],["attrition_by_department.csv","attrition_report.json"],["Compute department and global attrition measures from workforce records."]),
task("aggregate_engagement","Aggregate engagement surveys","temporal_aggregation",["input:engagement_surveys.csv","input:employees.csv"],["engagement_by_employee.csv"],["Validate employee membership/dates/scores and compute employee composites."]),
task("summarize_engagement","Summarize engagement by month","temporal_summary",["engagement_by_employee.csv","input:engagement_surveys.csv"],["engagement_by_month.csv","engagement_report.json"],["Compute month-level and global survey measures."]),
task("aggregate_performance","Aggregate performance reviews","grouped_aggregation",["input:performance_reviews.csv","input:employees.csv"],["performance_by_employee.csv"],["Validate employee membership and aggregate review measures per employee."]),
task("summarize_performance","Summarize performance by department","grouped_aggregation",["performance_by_employee.csv","input:employees.csv"],["performance_by_department.csv","performance_report.json"],["Attach departments and compute department/global performance measures."])]},

"009_healthcare_readmission":{
"title":"Patient readmission integration with model and descriptive branches","domain":"healthcare","family":"multisource_readmission_analysis","topology":"fan_in_fan_out","runner":"healthcare",
"reason":"Four patient-related sources must be independently prepared, joined once, and then reused by distinct model/utilization/clinical analyses before a final synthesis.",
"sources":{"patients.csv":("patients.csv","csv"),"admissions.csv":("admissions.json","json"),"lab_results.csv":("lab_results.json","json"),"medications.csv":("medications.xlsx","xlsx")},
"columns":{"patients.csv":["patient_id","age","gender","race","conditions","has_diabetes","has_heart_condition","bmi","smoker","insurance_type","n_conditions","readmitted_30d"],"admissions.csv":["admission_id","patient_id","length_of_stay","icu_stay","n_procedures","er_admission"],"lab_results.csv":["admission_id","patient_id","test_name","test_value","abnormal_flag"],"medications.csv":["admission_id","patient_id","medication"]},
"description":"""Build a `fan_in_fan_out` patient-analysis DAG. Four independently prepared sources converge into patient_features.csv. That table fans out to a fixed readmission model, a utilization comparison, and an insurance-group clinical summary. The three results reconverge into readmission_report.json. This is an experimental benchmark, not clinical guidance.

Require unique nonblank patient_id and admission_id keys, valid foreign keys from all events to patients and from labs/medications to admissions, finite required measures, and binary readmitted_30d. Emit patients_clean.csv. Aggregate admissions per patient into count, total/mean length of stay, ICU count, procedures, and ER count; labs into count, abnormal count, and mean test value; medications into record count and unique medication count.

Left-join all three summaries one-to-one to patients and fill absent aggregate measures with zero. Retain patient demographics, insurance_type, target, and all aggregate features in patient_features.csv sorted by patient_id.

Model branch: use the specified numeric patient and aggregate features, a 75/25 stratified split with seed 42, train-only StandardScaler, and LogisticRegression(C=1, liblinear, max_iter=1000, seed 42). Threshold at 0.5 and emit model.pkl, predictions.csv, and accuracy/precision/recall/F1/ROC-AUC in readmission_metrics.json.

Utilization branch groups by readmitted_30d into patient count and means for admission count, total stay, and ER count. Clinical branch groups by insurance_type into patient count, readmission rate, mean abnormal-lab count, and mean unique medications. The final report publishes source counts, nested model metrics, and group counts; it must consume all three branch results.""",
"artifacts":[artifact("patients_clean.csv",["patient_id","readmitted_30d"]),artifact("admissions_by_patient.csv",["patient_id","admission_count","total_length_of_stay"]),artifact("labs_by_patient.csv",["patient_id","lab_count","abnormal_lab_count"]),artifact("medications_by_patient.csv",["patient_id","medication_record_count","unique_medications"]),artifact("patient_features.csv",["patient_id","readmitted_30d","admission_count","lab_count","medication_record_count"]),artifact("model.pkl"),artifact("predictions.csv",["patient_id","actual_readmitted","readmission_probability","predicted_readmitted"]),artifact("readmission_metrics.json"),artifact("utilization_by_readmission.csv",["readmitted_30d","patient_count","mean_admission_count"]),artifact("clinical_summary.csv",["insurance_type","patient_count","readmission_rate"]),artifact("readmission_report.json")],
"tasks":[
task("prepare_patients","Validate patient records","source_validation",["input:patients.csv"],["patients_clean.csv"],["Validate patient keys, numeric measures, and binary target."]),
task("aggregate_admissions","Aggregate admissions by patient","event_aggregation",["input:admissions.csv","input:patients.csv"],["admissions_by_patient.csv"],["Validate admission/patient keys and compute declared utilization measures."]),
task("aggregate_labs","Aggregate laboratory results by patient","event_aggregation",["input:lab_results.csv","input:admissions.csv","input:patients.csv"],["labs_by_patient.csv"],["Validate event relationships and compute lab counts/means."]),
task("aggregate_medications","Aggregate medications by patient","event_aggregation",["input:medications.csv","input:admissions.csv","input:patients.csv"],["medications_by_patient.csv"],["Validate event relationships and compute medication counts."]),
task("integrate","Integrate patient feature branches","multiway_left_join",["patients_clean.csv","admissions_by_patient.csv","labs_by_patient.csv","medications_by_patient.csv"],["patient_features.csv"],["Left-join all summaries one-to-one and zero-fill absent aggregates."]),
task("model","Fit and evaluate readmission classifier","binary_classification",["patient_features.csv"],["model.pkl","predictions.csv","readmission_metrics.json"],["Apply the fixed stratified split, train-only scaling, model, threshold, and metrics."]),
task("utilization","Compare utilization by readmission status","grouped_aggregation",["patient_features.csv"],["utilization_by_readmission.csv"],["Compute the declared utilization measures by target group."]),
task("clinical","Summarize clinical burden by insurance","grouped_aggregation",["patient_features.csv"],["clinical_summary.csv"],["Compute the declared clinical measures by insurance type."]),
task("report","Synthesize readmission analyses","multi_input_report",["readmission_metrics.json","utilization_by_readmission.csv","clinical_summary.csv"],["readmission_report.json"],["Consume all three analytical branches and publish source/group/model results."])]},

"010_hr_regression_visualization_integration":{
"title":"Integrated workforce features with three analytical outputs","domain":"human_resources","family":"workforce_fanout_analysis","topology":"linear_to_fan_out","runner":"hr_fanout",
"reason":"Employee and department records share a common integration/feature prefix, after which salary modeling and two summaries are independent consumers.",
"sources":{"employees.csv":("employees.csv","csv"),"departments.csv":("departments.csv","csv")},
"columns":{"employees.csv":["emp_id","department","role","experience_years","education","performance_score","age","gender","salary"],"departments.csv":["department","headcount","budget_millions","location"]},
"description":"""Build a `linear_to_fan_out` workforce pipeline. Validate and integrate employee/department data, derive common features, then fan out to three independent leaves: salary regression, department summary, and gender pay summary. Do not add an artificial synthesis node.

Require unique nonblank emp_id and department keys, valid employee department membership, and finite numeric fields. Join employees many-to-one with departments and write workforce.csv sorted by emp_id. Derive salary_per_experience_year = salary/(experience_years+1) and budget_per_head_millions = budget_millions/headcount in workforce_features.csv.

Salary branch: predictors in order are experience_years, performance_score, age, headcount, budget_millions. Use an 80/20 random split with seed 42 and LinearRegression. Emit salary_model.pkl, sorted salary_predictions.csv, and salary_metrics.json with train/test rows, features, MAE, RMSE, and R2.

Department branch emits employee_rows, declared_headcount, budget_millions, mean_salary, and mean_performance_score by department. Gender branch emits employee_count, mean/median salary, and mean experience_years by gender. Both are sorted by group. These descriptive branches must consume workforce_features.csv directly and must not depend on the model branch.""",
"artifacts":[artifact("workforce.csv",["emp_id","department","headcount","budget_millions"]),artifact("workforce_features.csv",["emp_id","salary_per_experience_year","budget_per_head_millions"]),artifact("salary_model.pkl"),artifact("salary_predictions.csv",["emp_id","actual_salary","predicted_salary"]),artifact("salary_metrics.json"),artifact("department_summary.csv",["department","employee_rows","declared_headcount","mean_salary"]),artifact("gender_pay_summary.csv",["gender","employee_count","mean_salary","median_salary"] )],
"tasks":[
task("integrate","Validate and join employee/department sources","many_to_one_join",["input:employees.csv","input:departments.csv"],["workforce.csv"],["Validate source keys/measures and join employees many-to-one with departments."]),
task("features","Derive common workforce features","feature_engineering",["workforce.csv"],["workforce_features.csv"],["Compute salary-per-experience and budget-per-head exactly as specified."]),
task("salary_model","Fit and evaluate salary regression","supervised_regression",["workforce_features.csv"],["salary_model.pkl","salary_predictions.csv","salary_metrics.json"],["Use the fixed predictors, random split, LinearRegression, and held-out metrics."]),
task("department_summary","Summarize department workforce","grouped_aggregation",["workforce_features.csv"],["department_summary.csv"],["Compute the declared department measures."]),
task("gender_summary","Summarize pay by gender","grouped_aggregation",["workforce_features.csv"],["gender_pay_summary.csv"],["Compute the declared gender measures."])]},

"054_student_performance":{
"title":"Student GPA regression with explicit feature and evaluation stages","domain":"education","family":"student_supervised_regression","topology":"linear","runner":"students",
"reason":"A single table and one fixed modeling objective form an honest linear workflow and provide the batch's sole chain topology.",
"sources":{"data.csv":("data.csv","csv")},
"columns":{"data.csv":["student_id","major","year","age","study_hours_per_week","attendance_pct","previous_gpa","current_gpa","assignments_completed","extracurricular_hours"]},
"description":"""Build the batch's sole `linear` pipeline: validate student records, derive features, split, fit/predict, evaluate, and report. Require unique nonblank student_id, finite numeric fields, attendance in [0,100], and previous/current GPA in [0,4]. Sort students_clean.csv by student_id.

Derive study_attendance_interaction = study_hours_per_week*attendance_pct/100 and gpa_change = current_gpa-previous_gpa. The target is current_gpa; gpa_change is retained for audit but must not be a predictor. Use predictors in this order: year, age, study_hours_per_week, attendance_pct, previous_gpa, assignments_completed, extracurricular_hours, study_attendance_interaction.

Create an 80/20 random split with seed 42 and sort the emitted train.csv/test.csv by student_id. Fit StandardScaler on training predictors only, then Ridge(alpha=1, solver=svd). Emit model.pkl and predictions.csv for every test student. metrics.json contains train/test counts, ordered features, MAE, and RMSE; student_report.json publishes exactly those computed values. Every stage consumes the preceding stage's artifacts.""",
"artifacts":[artifact("students_clean.csv",["student_id","current_gpa"]),artifact("student_features.csv",["student_id","study_attendance_interaction","gpa_change"]),artifact("train.csv",["student_id","current_gpa"]),artifact("test.csv",["student_id","current_gpa"]),artifact("model.pkl"),artifact("predictions.csv",["student_id","actual_gpa","predicted_gpa"]),artifact("metrics.json"),artifact("student_report.json")],
"tasks":[
task("validate","Validate student records","source_validation",["input:data.csv"],["students_clean.csv"],["Validate keys, numeric fields, attendance, and GPA bounds."]),
task("features","Derive student predictors","feature_engineering",["students_clean.csv"],["student_features.csv"],["Compute the two declared features without target leakage."]),
task("split","Create reproducible train/test partitions","random_split",["student_features.csv"],["train.csv","test.csv"],["Use an 80/20 split with seed 42 and preserve all rows."],{"test_fraction":.2,"random_state":42}),
task("fit_predict","Fit training-only Ridge pipeline","supervised_regression",["train.csv","test.csv"],["model.pkl","predictions.csv"],["Fit scaler/model on training rows only and predict each test row."],{"estimator":"Ridge","alpha":1.0,"solver":"svd"}),
task("evaluate","Measure held-out GPA errors","regression_evaluation",["predictions.csv"],["metrics.json"],["Compute MAE/RMSE and retain split/feature metadata."]),
task("report","Publish student model report","model_report",["metrics.json"],["student_report.json"],["Publish exactly the computed evaluation values."])]}
}


def save(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+"\n")


def convert(source,kind,destination):
    if kind=="csv":shutil.copyfile(source,destination)
    elif kind=="json":pd.read_json(source).to_csv(destination,index=False)
    elif kind=="xlsx":pd.read_excel(source).to_csv(destination,index=False)
    else:raise ValueError(kind)


def main():
    reference=(ROOT/"tools"/"batch03_reference.py").read_text();batch=[]
    for name,case in CASES.items():
        destination=ROOT/"pipelines"/name;inputs_dir=destination/"inputs";inputs_dir.mkdir(parents=True,exist_ok=True);conversions=[]
        for output_name,(source_name,kind) in case["sources"].items():
            convert(UPSTREAM/name/"data"/source_name,kind,inputs_dir/output_name);conversions.append({"source":source_name,"benchmark_file":output_name,"conversion":f"{kind}_to_csv" if kind!="csv" else "byte_copy"})
        inputs=[{"id":"input:"+filename,"path":"inputs/"+filename,"format":"csv","required_columns":columns} for filename,columns in case["columns"].items()]
        producers={output:item["id"] for item in case["tasks"] for output in item["outputs"]};dependencies=[]
        for item in case["tasks"]:
            for parent in sorted({producers[value] for value in item["inputs"] if value in producers}):
                dependencies.append({"source":parent,"target":item["id"],"kind":"data","artifacts":[value for value in item["inputs"] if producers.get(value)==parent]})
        graph={"schema_version":"inlumen.benchmark.task-graph@2","pipeline_id":name,"benchmark_revision":"batch-03","review_status":"author_review_pending","title":case["title"],"domain":case["domain"],"family_id":case["family"],"topology":case["topology"],"inputs":inputs,"tasks":case["tasks"],"artifacts":case["artifacts"],"dependencies":dependencies,"rq1_policy":{"task_matching":"reviewed_semantic_mapping","allow_split_or_merge":True,"exact_node_count_required":False,"data_edges_require_artifact_binding":True,"unknown_semantics":"unassessed_not_pass"},"reference":{"entrypoint":"reference.py","task_functions":{item["id"]:case["runner"] for item in case["tasks"]}},"numeric_tolerance":{"atol":1e-6,"rtol":1e-6}}
        outputs="\n".join(f"- `{item['path']}`" for item in case["artifacts"]);(destination/"description.md").write_text(f"# {case['title']}\n\n{case['description'].strip()}{COMMON}{outputs}\n")
        save(destination/"task_graph.json",graph);(destination/"reference.py").write_text(reference);(destination/"requirements.txt").write_text("numpy==2.0.1\npandas==2.2.2\nscikit-learn==1.5.1\nopenpyxl==3.1.5\n")
        hashes={path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(inputs_dir.iterdir())};save(destination/"provenance.json",{"upstream_repository":"https://github.com/aliduabubakari/custom-pipelines","upstream_commit":REV,"upstream_pipeline":name,"selection_reason":case["reason"],"input_transformations":conversions,"pilot_input_sha256":hashes,"description_status":"behaviorally_rewritten_for_evaluation","review_status":"author_review_pending"})
        batch.append({"pipeline_id":name,"title":case["title"],"domain":case["domain"],"family_id":case["family"],"topology":case["topology"],"task_count":len(case["tasks"]),"review_status":"author_review_pending"})
    save(ROOT/"batch-03.json",{"batch_id":"batch-03","case_count":len(batch),"topology_policy":{"linear_cases":1,"required_distinct_topologies":5},"cases":batch});print(f"Prepared {len(batch)} cases at upstream revision {REV}")


if __name__=="__main__":main()
