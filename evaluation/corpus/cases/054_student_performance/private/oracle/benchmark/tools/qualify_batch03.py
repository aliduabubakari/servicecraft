"""Qualify batch-03 behavior, topology, failure handling, and exports."""
import copy
import hashlib
import json
from importlib.metadata import version
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

from export_inputs import export
from validate_specs import ROOT, validate

CASES=["001_analytics_statistical_cleaning_integration","007_employee_attrition","009_healthcare_readmission","010_hr_regression_visualization_integration","054_student_performance"]


def load(path):
    def reject(value):raise ValueError("non-finite JSON: "+value)
    return json.loads(path.read_text(),parse_constant=reject)


def run(case,data,out,expect_failure=False):
    out.mkdir();result=subprocess.run([sys.executable,str(ROOT/"pipelines"/case/"reference.py"),"--data-dir",str(data),"--output-dir",str(out)],capture_output=True,text=True)
    if expect_failure:
        assert result.returncode!=0,f"{case} accepted invalid data";return
    if result.returncode:raise RuntimeError(result.stderr)
    graph=load(ROOT/"pipelines"/case/"task_graph.json")
    for item in graph["artifacts"]:
        path=out/item["path"];assert path.is_file(),path
        if path.suffix==".csv":assert set(item["required_columns"])<=set(pd.read_csv(path,nrows=0).columns)
        elif path.suffix==".json":load(path)


def check_finance(data,out):
    source=pd.read_csv(data/"stocks.csv");clean=pd.read_csv(out/"clean_stocks.csv");market=pd.read_csv(data/"market_indices.csv");panel=pd.read_csv(out/"market_panel.csv")
    expected_high=source[["open","high","low","close"]].max(axis=1);expected_low=source[["open","high","low","close"]].min(axis=1)
    keyed=clean.merge(source[["ticker","date"]].assign(source_row=range(len(source))),on=["ticker","date"],validate="one_to_one")
    np.testing.assert_allclose(keyed.high,expected_high.iloc[keyed.source_row]);np.testing.assert_allclose(keyed.low,expected_low.iloc[keyed.source_row])
    assert len(panel)==len(source) and panel.date.nunique()==len(market)
    for _,group in panel.groupby("ticker"):
        expected=group.close.pct_change();np.testing.assert_allclose(group.stock_return.iloc[1:],expected.iloc[1:])
    report=load(out/"finance_report.json");assert report["tickers"]==source.ticker.nunique() and report["matched_dates"]==len(market)


def check_parallel(data,out):
    employees=pd.read_csv(data/"employees.csv");surveys=pd.read_csv(data/"engagement_surveys.csv");reviews=pd.read_csv(data/"performance_reviews.csv")
    attrition=pd.read_csv(out/"attrition_by_department.csv");monthly=pd.read_csv(out/"engagement_by_month.csv");performance=pd.read_csv(out/"performance_by_employee.csv")
    assert attrition.employee_count.sum()==len(employees);assert attrition.attrition_count.sum()==employees.is_attrited.sum()
    assert monthly.survey_count.sum()==len(surveys);assert performance.review_count.sum()==len(reviews)
    graph=load(ROOT/"pipelines"/"007_employee_attrition"/"task_graph.json");profile=validate(graph,ROOT/"pipelines"/"007_employee_attrition")["structure"]
    assert profile=={"components":3,"roots":3,"sinks":3,"joins":0,"splits":0}


def check_health(data,out):
    patients=pd.read_csv(data/"patients.csv");admissions=pd.read_csv(data/"admissions.csv");labs=pd.read_csv(data/"lab_results.csv");meds=pd.read_csv(data/"medications.csv")
    features=pd.read_csv(out/"patient_features.csv");pred=pd.read_csv(out/"predictions.csv")
    assert len(features)==len(patients) and features.patient_id.is_unique
    np.testing.assert_allclose(features.admission_count.sum(),len(admissions));np.testing.assert_allclose(features.lab_count.sum(),len(labs));np.testing.assert_allclose(features.medication_record_count.sum(),len(meds))
    assert len(pred)==125 and pred.readmission_probability.between(0,1).all()
    report=load(out/"readmission_report.json");assert report["patients"]==len(patients) and report["admissions"]==len(admissions) and report["labs"]==len(labs) and report["medication_records"]==len(meds)


def check_hr(data,out):
    employees=pd.read_csv(data/"employees.csv");workforce=pd.read_csv(out/"workforce_features.csv");department=pd.read_csv(out/"department_summary.csv");gender=pd.read_csv(out/"gender_pay_summary.csv")
    assert len(workforce)==len(employees);np.testing.assert_allclose(workforce.salary_per_experience_year,workforce.salary/(workforce.experience_years+1));np.testing.assert_allclose(workforce.budget_per_head_millions,workforce.budget_millions/workforce.headcount)
    assert department.employee_rows.sum()==len(employees) and gender.employee_count.sum()==len(employees)
    metrics=load(out/"salary_metrics.json");assert metrics["train_rows"]==320 and metrics["test_rows"]==80


def check_students(data,out):
    source=pd.read_csv(data/"data.csv");features=pd.read_csv(out/"student_features.csv");train=pd.read_csv(out/"train.csv");test=pd.read_csv(out/"test.csv");pred=pd.read_csv(out/"predictions.csv")
    np.testing.assert_allclose(features.study_attendance_interaction,features.study_hours_per_week*features.attendance_pct/100);np.testing.assert_allclose(features.gpa_change,features.current_gpa-features.previous_gpa)
    assert len(train)==240 and len(test)==len(pred)==60;assert set(train.student_id).isdisjoint(test.student_id) and set(train.student_id)|set(test.student_id)==set(source.student_id)
    assert load(out/"metrics.json")==load(out/"student_report.json")


CHECKERS={CASES[0]:check_finance,CASES[1]:check_parallel,CASES[2]:check_health,CASES[3]:check_hr,CASES[4]:check_students}


def corrupt(case,source,destination):
    shutil.copytree(source,destination)
    if case==CASES[0]:
        path=destination/"market_indices.csv";frame=pd.read_csv(path);frame=pd.concat([frame,frame.iloc[[0]]],ignore_index=True)
    elif case==CASES[1]:
        path=destination/"engagement_surveys.csv";frame=pd.read_csv(path);frame.loc[0,"employee_id"]="UNKNOWN"
    elif case==CASES[2]:
        path=destination/"medications.csv";frame=pd.read_csv(path);frame.loc[0,"admission_id"]="UNKNOWN"
    elif case==CASES[3]:
        path=destination/"employees.csv";frame=pd.read_csv(path);frame.loc[0,"department"]="UNKNOWN"
    else:
        path=destination/"data.csv";frame=pd.read_csv(path);frame.loc[1,"student_id"]=frame.loc[0,"student_id"]
    frame.to_csv(path,index=False)


def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix="inlumen-batch03-") as temp_name:
        temp=Path(temp_name)
        for case in CASES:
            source=ROOT/"pipelines"/case;validation=validate(load(source/"task_graph.json"),source)
            out=temp/(case+"-output");run(case,source/"inputs",out);CHECKERS[case](source/"inputs",out)
            results.append({"case":case,"probe":"reference_outputs_independent_invariants_and_topology","status":"passed","topology":validation["topology"],"tasks":validation["tasks"],"structure":validation["structure"],"output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}})
            invalid=temp/(case+"-invalid");corrupt(case,source/"inputs",invalid);run(case,invalid,temp/(case+"-invalid-output"),expect_failure=True);results.append({"case":case,"probe":"invalid_key_relationship_rejected","status":"passed"})
            for track in ["natural_language","fixed_graph"]:
                destination=export(case,temp/f"{case}-{track}",track);files={str(path.relative_to(destination)) for path in destination.rglob("*") if path.is_file()}
                assert not any(Path(path).name in {"reference.py","task_graph.json","provenance.json","requirements.txt"} for path in files);assert ("provided_graph.json" in files)==(track=="fixed_graph")
        for case in CASES:
            graph=load(ROOT/"pipelines"/case/"task_graph.json");wrong=copy.deepcopy(graph);wrong["topology"]="linear" if graph["topology"]!="linear" else "fan_out"
            try:validate(wrong)
            except AssertionError:pass
            else:raise AssertionError(f"wrong topology accepted for {case}")
        results.append({"case":"batch-03","probe":"incorrect_topology_labels_rejected","status":"passed"})
        results.append({"case":"batch-03","probe":"generator_input_allowlist_both_tracks","status":"passed"})
    report={"status":"passed","scope":"Batch-03 Python references, independent invariants, invalid-key rejection, topology classification, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation","dagster_runtime_qualification":"not_run","review_status":"author_review_pending","python":sys.version.split()[0],"packages":{name:version(name) for name in ["pandas","numpy","scikit-learn","jsonschema"]},"checks":results}
    (ROOT/"qualification-report-batch03.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({"status":"passed","check_groups":len(results),"dagster_runtime_qualification":"not_run"},indent=2))


if __name__=="__main__":main()
