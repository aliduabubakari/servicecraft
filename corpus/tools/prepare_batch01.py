"""Materialize the documented pilot fixtures/specs from the unchanged upstream checkout."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'custom-pipelines'
REV = subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip()

def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')

def artifact(name, columns=None):
    return {'id': name, 'path': name, 'format': Path(name).suffix[1:], 'required_columns': columns or []}

def task(id, name, operation, inputs, outputs, requirements, parameters=None):
    return {'id': id, 'name': name, 'operation': operation, 'required': True, 'inputs': inputs, 'outputs': outputs,
            'requirements': requirements, 'parameters': parameters or {}}

SPORTS = '042_sports_validation_recovery'
GEO = '058_transportation_cleaning_integration_geospatial'
ENERGY = '008_energy_forecasting'

cases = {
SPORTS: {
 'title': 'Sports roster validation and deterministic recovery', 'domain':'sports', 'family':'validation_groupwise_recovery',
 'reason':'The upstream recovery/validation label describes a generic regression workflow and does not define a recovery policy.',
 'description': '''Build a local Dagster pipeline that prepares a trustworthy sports roster and produces a data-derived quality report. This is a data validation and recovery task; it requires no predictive model or visualization.

Input `data.csv` contains player_id, team, position, games_played, points_per_game, minutes_per_game, and additional unused fields. Use the six named fields. Preserve the original one-based source row for audit. Strip whitespace from the three string fields; a whitespace-only string is missing. Replace missing team/position with the literal Unknown. Coerce invalid numeric text to missing values.

Reject rows with a missing player ID, a repeated normalized player ID after its first occurrence in input order, or games_played that is non-finite, non-integer, or outside [0,82]. For a row with several defects, use exactly one rejection reason in this priority: missing_player_id, duplicate_player_id, invalid_games_played. Duplicate detection uses the first input occurrence even if that occurrence is subsequently rejected.

On eligible rows, treat non-finite or negative points_per_game as missing. Treat non-finite minutes_per_game or values outside [0,48] as missing. Recover each field using the median of valid eligible values within the normalized position. If a group has no valid value, use the global median of valid eligible values for that field. If none exist globally, use zero. Compute all medians from the values before recovery. Do not change valid numeric values, cap outliers, or drop recoverable rows. Derive total_points = games_played * recovered points_per_game. Sort recovered rows lexicographically by player_id.

Produce the normalized, eligible, rejected, and recovered tables and the audit JSON files specified below. The final quality_report.json must contain input_rows, eligible_rows, rejected_rows, rejection_counts (nonzero reason counts), imputed_cells (counts for both recovered fields), players, total_points, and players_per_team. Counts must reconcile and report values must be computed from this execution's data. Reject records need source_row and reason so omissions are auditable. No timestamp or fixed recommendations are required.

Validation must precede recovery; the report must consume the recovered data and its recovery audit. Preserve intermediate artifacts so the evaluator can distinguish wrong eligibility, wrong recovery, and wrong reporting.''',
 'input_columns':{'data.csv':['player_id','team','position','games_played','points_per_game','minutes_per_game']},
 'artifacts': [artifact('normalized.csv',['source_row','player_id','team','position','games_played','points_per_game','minutes_per_game']), artifact('eligible.csv',['source_row','player_id','team','position','games_played','points_per_game','minutes_per_game']), artifact('rejected.csv',['source_row','player_id','reason']), artifact('validation.json'), artifact('recovered.csv',['source_row','player_id','team','position','games_played','points_per_game','minutes_per_game','total_points']), artifact('recovery.json'), artifact('quality_report.json')],
 'tasks':[
 task('normalize','Normalize roster fields','normalize_records',['input:data.csv'],['normalized.csv'],['Trim string fields and retain source_row.','Select the six named fields and coerce numeric text.','Replace missing team/position with Unknown.']),
 task('validate','Identify eligible and rejected rows','validate_and_partition',['normalized.csv'],['eligible.csv','rejected.csv','validation.json'],['Apply missing ID, duplicate ID, and games rules with the stated reason priority.','Convert invalid recovery fields to missing without rejecting their rows.'],{'games_min':0,'games_max':82,'minutes_min':0,'minutes_max':48,'duplicate_policy':'first_input_occurrence'}),
 task('recover','Recover missing measures and derive totals','groupwise_imputation',['eligible.csv','validation.json'],['recovered.csv','recovery.json'],['Use pre-recovery position medians with global median then zero fallback.','Preserve valid values and compute total_points.'],{'group_by':'position','strategy':'median','fields':['points_per_game','minutes_per_game'],'fallback':['global_median',0],'sort_by':'player_id'}),
 task('report','Produce quality and roster summary','quality_report',['recovered.csv','recovery.json'],['quality_report.json'],['Reconcile input/eligible/rejected counts and report both imputation counts.','Compute team counts and total points from recovered rows.'])],
},
GEO: {
 'title':'Transportation spatial enrichment and route aggregation','domain':'transportation','family':'spatial_etl_grouped_aggregation',
 'reason':'The upstream geospatial label lacks a specified spatial computation and its generic model predicts destination longitude.',
 'description':'''Build a local Dagster pipeline for spatial enrichment of transportation trips and route-level analysis. It requires actual spherical distance computation and grouped summaries, with no machine learning or visualization.

Read `data.csv`. Use trip_id, route, origin_lat, origin_lon, dest_lat, dest_lon, distance_km, passengers, and delay_minutes; ignore other columns. Strip whitespace from trip_id/route and treat blanks as missing. Coerce numeric text to numbers. Reject a row if either string is missing, its normalized trip_id repeats after the first input occurrence, any required numeric value is missing/non-finite, latitude is outside [-90,90], longitude outside [-180,180], distance_km/passengers/delay_minutes is negative, or passengers is not an integer. A duplicate's first occurrence is defined before validity filtering. Do not impute invalid coordinates or clip them. Keep rejected rows in rejected_trips.csv and record input_rows, valid_rows, and rejected_rows in validation.json.

For valid trips compute great_circle_km using the haversine formula on origin/destination coordinates in degrees with spherical Earth radius 6371.0088 km. Clip the formula's intermediate a to [0,1] before computing 2R*asin(sqrt(a)). Compute passenger_km = distance_km * passengers and detour_ratio = distance_km / great_circle_km. If great_circle_km is exactly zero, write a missing detour_ratio rather than infinity. distance_km is a supplied traveled distance; do not replace it with spherical distance. Synthetic trips may have detour_ratio below one, which must not be clipped or rejected. Sort trip_metrics.csv by trip_id.

Group valid enriched trips by normalized route. For each route output trip_count, mean_great_circle_km, total_passenger_km, and mean_delay_minutes. Sort route_summary.csv by route. Produce spatial_report.json with quality (the input/valid/rejected counts), earth_radius_km, route_count, total_passenger_km over all valid trips, mean_great_circle_km over all valid trips (null for an empty set), and top_routes containing up to five route names ranked by descending trip_count with lexicographically ascending route as the tie-breaker. Empty valid data must yield an empty route table, zero total passenger-km, null mean distance, and an empty top_routes array.

Validation precedes spatial enrichment, route aggregation consumes enriched trips, and reporting consumes the computed aggregation. Preserve validation and spatial metadata through the intermediate JSON artifacts listed below. Every required result must come from the current run.''',
 'input_columns':{'data.csv':['trip_id','route','origin_lat','origin_lon','dest_lat','dest_lon','distance_km','passengers','delay_minutes']},
 'artifacts':[artifact('valid_trips.csv',['trip_id','route','origin_lat','origin_lon','dest_lat','dest_lon','distance_km','passengers','delay_minutes']),artifact('rejected_trips.csv',['trip_id']),artifact('validation.json'),artifact('trip_metrics.csv',['trip_id','great_circle_km','passenger_km','detour_ratio']),artifact('spatial_metadata.json'),artifact('route_summary.csv',['route','trip_count','mean_great_circle_km','total_passenger_km','mean_delay_minutes']),artifact('aggregate.json'),artifact('spatial_report.json')],
 'tasks':[
 task('validate','Validate trip identities, measures and coordinates','validate_and_partition',['input:data.csv'],['valid_trips.csv','rejected_trips.csv','validation.json'],['Reject invalid coordinates/measurements, missing identities, and duplicate trip IDs.','Retain valid and rejected partitions and reconcile counts.']),
 task('spatial','Compute spherical and traveled-distance features','spatial_enrichment',['valid_trips.csv','validation.json'],['trip_metrics.csv','spatial_metadata.json'],['Apply haversine with the specified radius.','Compute passenger-km and zero-safe detour ratio; preserve quality metadata.'],{'earth_radius_km':6371.0088,'zero_distance_ratio':None,'sort_by':'trip_id'}),
 task('aggregate','Aggregate trip metrics by route','grouped_aggregation',['trip_metrics.csv','spatial_metadata.json'],['route_summary.csv','aggregate.json'],['Compute the specified route counts, means and sums.','Compute global measures and count-ranked routes with deterministic ties.'],{'group_by':'route','top_k':5,'rank':['trip_count_desc','route_asc']}),
 task('report','Publish spatial analysis summary','aggregate_report',['aggregate.json'],['spatial_report.json'],['Publish data-derived global measures, quality counts, radius and top routes, including empty-set behavior.'])],
},
ENERGY: {
 'title':'Energy demand regression with lagged weather and chronological evaluation','domain':'energy','family':'temporal_multisource_supervised_regression',
 'reason':'The upstream target fallback can choose an unintended numeric column; random splitting and pre-split scaling weaken forecasting semantics.',
 'description':'''Build a local Dagster pipeline to evaluate historical hourly energy demand regression with lagged information. The target is exactly consumption_kwh. This evaluates fixed-model rolling prediction with observed lagged consumption, not recursive multi-hour forecasting or a production forecast service.

Read energy_consumption.csv (timestamp, consumption_kwh, is_holiday) and weather.csv (date, temp_avg, humidity_avg, cloud_cover_avg, wind_avg); ignore all other fields. Parse timestamps/dates, sort energy by timestamp and weather by date, and fail on duplicate timestamps/dates, missing or non-finite required numeric values, negative consumption, or holiday flags outside {0,1}. Energy observations must be continuous at one-hour intervals. Dates are timezone-naive and weather.date is a calendar-day key. Inputs that violate these preconditions fail clearly; do not silently fill or drop malformed source observations.

For each energy observation on date D, left-join weather from D-1 using one daily weather row per key. Name the joined fields previous_temp_avg, previous_humidity_avg, previous_cloud_cover_avg, previous_wind_avg. Do not use same-day or future weather, the hourly weather fields embedded in energy_consumption.csv, or weather.is_holiday. Derive lag_24h_kwh from consumption exactly 24 preceding hourly rows, hour (0-23), day_of_week (Monday=0), and month (1-12). Use the energy input's is_holiday unchanged. After deriving lag/joins, omit feature rows missing any required predictor. Require at least 10 eligible observations.

Use exactly these predictors in this order: lag_24h_kwh, hour, day_of_week, month, is_holiday, previous_temp_avg, previous_humidity_avg, previous_cloud_cover_avg, previous_wind_avg. Retain timestamp and consumption_kwh for audit but exclude them from predictors. Sort chronologically and split the eligible rows at floor(0.8*N): earliest rows train, remaining rows test. Do not shuffle. Lagged consumption in later test observations may use earlier observed consumption from the test period, because this is rolling prediction, not a recursive forecast.

Fit StandardScaler (population variance, ddof=0) on training predictors only, then Ridge regression with alpha=1, fit_intercept=True, and solver=svd on the scaled training predictors and training target. Reuse the fitted scaler on test data. Save a pickle of the fitted pipeline and fit_metadata.json with train_rows, test_rows, the ordered feature list, alpha, scaler_mean, and scaler_scale. Do not fit preprocessing on all data or include the target as a predictor.

Write predictions.csv containing timestamp, actual_kwh, predicted_kwh for every test row in chronological order. Compute MAE and RMSE in kWh directly from these held-out predictions. metrics.json must include the fit metadata plus mae_kwh and rmse_kwh. energy_report.json must publish those computed values. Preserve the intermediate aligned/feature/train/test tables so lag choice, split boundary, and leakage can be independently checked. This task specifies an estimator and procedure, rather than a loose model-quality threshold.''',
 'input_columns':{'energy_consumption.csv':['timestamp','consumption_kwh','is_holiday'],'weather.csv':['date','temp_avg','humidity_avg','cloud_cover_avg','wind_avg']},
 'artifacts':[artifact('hourly.csv',['timestamp','consumption_kwh','is_holiday']),artifact('daily_weather.csv',['date','temp_avg','humidity_avg','cloud_cover_avg','wind_avg']),artifact('aligned.csv',['timestamp','previous_temp_avg']),artifact('features.csv',['timestamp','consumption_kwh','lag_24h_kwh','hour','day_of_week','month','is_holiday','previous_temp_avg','previous_humidity_avg','previous_cloud_cover_avg','previous_wind_avg']),artifact('train.csv',['timestamp','consumption_kwh']),artifact('test.csv',['timestamp','consumption_kwh']),artifact('model.pkl'),artifact('predictions.csv',['timestamp','actual_kwh','predicted_kwh']),artifact('fit_metadata.json'),artifact('metrics.json'),artifact('energy_report.json')],
 'tasks':[
 task('ingest','Validate and order energy and weather sources','multisource_ingestion',['input:energy_consumption.csv','input:weather.csv'],['hourly.csv','daily_weather.csv'],['Select named fields; parse keys, sort, and validate continuity, uniqueness and numeric source preconditions.']),
 task('align','Align observations with preceding-day weather','temporal_join',['hourly.csv','daily_weather.csv'],['aligned.csv'],['Left join the calendar date to D-1 daily weather with many-to-one cardinality.'],{'weather_day_offset':-1,'join':'left','cardinality':'many_to_one'}),
 task('features','Derive lagged and calendar predictors','temporal_features',['aligned.csv'],['features.csv'],['Construct the exact predictor set and retain target/timestamp outside it.','Drop missing predictor rows only after deriving lag and joins.'],{'consumption_lag_hours':24,'weekday_origin':'Monday=0','minimum_eligible_rows':10}),
 task('split','Create chronological training and test partitions','temporal_split',['features.csv'],['train.csv','test.csv'],['Use earliest floor(0.8*N) eligible rows for training and all remaining rows for testing, without shuffling.'],{'train_fraction':0.8,'rounding':'floor','shuffle':False}),
 task('fit_predict','Fit train-only preprocessing and Ridge; predict test demand','supervised_regression',['train.csv','test.csv'],['model.pkl','predictions.csv','fit_metadata.json'],['Fit scaler and model exclusively on training rows.','Predict every test row with the fitted pipeline; save model and preprocessing metadata.'],{'estimator':'Ridge','alpha':1.0,'fit_intercept':True,'solver':'svd','scaler':'StandardScaler','scaler_ddof':0,'scaler_fit_rows':'train_only','target':'consumption_kwh','feature_columns':['lag_24h_kwh','hour','day_of_week','month','is_holiday','previous_temp_avg','previous_humidity_avg','previous_cloud_cover_avg','previous_wind_avg']}),
 task('evaluate','Measure held-out regression errors','regression_evaluation',['predictions.csv','fit_metadata.json'],['metrics.json'],['Compute MAE/RMSE from actual and predicted test demand; retain fit metadata.'],{'metrics':['mae_kwh','rmse_kwh']}),
 task('report','Publish demand evaluation summary','model_report',['metrics.json'],['energy_report.json'],['Publish computed model evaluation and fit metadata.'])],
}}

COMMON = '''

Execution and output contract: generate executable Dagster code using local files, without network access or external services. Each mandatory logical operation must be inspectable in the pipeline design/code. A different task decomposition is allowed if it preserves the stated behavior, dependencies, and observable intermediate outputs. Write outputs beneath the designated run output directory. Do not read outputs from previous runs. Preserve full numeric precision in CSV/JSON; numeric comparisons use atol=1e-6 and rtol=1e-6. JSON must not contain NaN or Infinity; missing CSV values may use empty cells. Required JSON counts are integers. Files listed below are mandatory checkpoints and results, not prescriptions for the number of Dagster assets. Missing input columns fail clearly.

Mandatory output files:
'''

for name,c in cases.items():
    dest = ROOT/'pipelines'/name
    (dest/'inputs').mkdir(parents=True, exist_ok=True)
    mutations=[]
    for filename in c['input_columns']:
        source = UPSTREAM/name/'data'/filename
        shutil.copyfile(source,dest/'inputs'/filename)
    if name == SPORTS:
        path=dest/'inputs/data.csv';df=pd.read_csv(path)
        df.loc[0,'points_per_game']=float('nan');df.loc[1,'minutes_per_game']=float('nan');df.loc[2,'games_played']=-1;df.loc[3,'player_id']=' '
        df.loc[4,'team']='  '+str(df.loc[4,'team'])+'  ';df.loc[4,'position']=' '
        df=pd.concat([df,df.iloc[[5]]],ignore_index=True);df.to_csv(path,index=False)
        mutations=['Row 1 points_per_game missing','Row 2 minutes_per_game missing','Row 3 games_played=-1','Row 4 player_id blank','Row 5 padded team and missing position','Append a duplicate of original row 6']
    if name == GEO:
        path=dest/'inputs/data.csv';df=pd.read_csv(path);df.loc[0,'origin_lat']=95;df.loc[1,'dest_lon']=float('nan');df.to_csv(path,index=False)
        mutations=['Row 1 origin_lat=95 (invalid)','Row 2 dest_lon missing']
    inputs=[{'id':'input:'+f,'path':'inputs/'+f,'format':'csv','required_columns':cols} for f,cols in c['input_columns'].items()]
    producers={a:t['id'] for t in c['tasks'] for a in t['outputs']}
    dependencies=[]
    for t in c['tasks']:
        parents={producers[a] for a in t['inputs'] if a in producers}
        for parent in sorted(parents):
            dependencies.append({'source':parent,'target':t['id'],'kind':'data','artifacts':[a for a in t['inputs'] if producers.get(a)==parent]})
    graph={'schema_version':'inlumen.benchmark.task-graph@2','pipeline_id':name,'benchmark_revision':'pilot-01','review_status':'author_review_pending','title':c['title'],'domain':c['domain'],'family_id':c['family'],'topology':'linear','inputs':inputs,'tasks':c['tasks'],'artifacts':c['artifacts'],'dependencies':dependencies,
           'rq1_policy':{'task_matching':'reviewed_semantic_mapping','allow_split_or_merge':True,'exact_node_count_required':False,'data_edges_require_artifact_binding':True,'unknown_semantics':'unassessed_not_pass'},
           'reference':{'entrypoint':'reference.py','task_functions':{t['id']:t['id'] for t in c['tasks']}},
           'numeric_tolerance':{'atol':1e-6,'rtol':1e-6}}
    save(dest/'task_graph.json',graph)
    outputs=''.join('- `'+a['path']+'`'+(' (required columns: '+', '.join(a['required_columns'])+')' if a['required_columns'] else '')+'\n' for a in c['artifacts'])
    (dest/'description.md').write_text('# '+c['title']+'\n\n'+c['description']+COMMON+outputs)
    provenance={'upstream_repository':'https://github.com/aliduabubakari/custom-pipelines','upstream_commit':REV,'source_pipeline':name,'change_kind':'new_behavioral_variant_not_equivalent_to_original','selection_reason':c['reason'],'input_modifications':mutations,'source_input_sha256':{},'pilot_input_sha256':{},'review_status':'author_review_pending'}
    for f in c['input_columns']:
        provenance['source_input_sha256'][f]=hashlib.sha256((UPSTREAM/name/'data'/f).read_bytes()).hexdigest()
        provenance['pilot_input_sha256'][f]=hashlib.sha256((dest/'inputs'/f).read_bytes()).hexdigest()
    save(dest/'provenance.json',provenance)
    (dest/'requirements.txt').write_text('numpy==2.3.1\npandas==2.3.0\n'+('scipy==1.16.0\nscikit-learn==1.7.0\n' if name==ENERGY else ''))

save(ROOT/'batch-01.json',{'batch_id':'batch-01','revision':'pilot-01','created_date':'2026-10-30','status':'author_review_pending','case_count':len(cases),'cases':[{'pipeline_id':name,'title':case['title'],'domain':case['domain'],'family_id':case['family'],'topology':'linear','task_count':len(case['tasks']),'review_status':'author_review_pending'} for name,case in cases.items()],'upstream_commit':REV,'changes':'Explicitly revised behavioral variants; not just annotations of original scripts.','dagster_runtime_qualification':'not_run','reference_runtime':'Python 3.12; see qualification-report.json'})
print('Prepared',len(cases),'pilot cases under',ROOT)
