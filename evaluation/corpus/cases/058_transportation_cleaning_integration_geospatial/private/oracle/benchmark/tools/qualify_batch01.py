"""Reference qualification with independent behavioral calculations and defect probes.

This qualifies Python reference behavior, not Dagster execution or generated candidates.
All run outputs are temporary. The saved report contains statuses and output hashes.
"""
import copy
import csv
import hashlib
import json
import math
import pickle
from importlib.metadata import version
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from validate_specs import ROOT, validate
from export_inputs import export

S='042_sports_validation_recovery';G='058_transportation_cleaning_integration_geospatial';E='008_energy_forecasting'
FEATURES=['lag_24h_kwh','hour','day_of_week','month','is_holiday','previous_temp_avg','previous_humidity_avg','previous_cloud_cover_avg','previous_wind_avg']


def load(path):
    def reject(value):
        raise ValueError('Non-finite JSON constant: '+value)
    return json.loads(path.read_text(),parse_constant=reject)


def close(a,b):
    assert math.isclose(float(a),float(b),rel_tol=1e-6,abs_tol=1e-6), (a,b)


def number(value):
    try:
        value=float(value)
        return value if math.isfinite(value) else None
    except (TypeError,ValueError):
        return None


def check_sports(data,out):
    rows=list(csv.DictReader((data/'data.csv').open()))
    eligible=[];rejected=[];seen=set();reasons={}
    for ix,row in enumerate(rows,1):
        id=row['player_id'].strip();team=row['team'].strip() or 'Unknown';position=row['position'].strip() or 'Unknown'
        games=number(row['games_played'])
        reason='missing_player_id' if not id else 'duplicate_player_id' if id in seen else 'invalid_games_played' if games is None or not (0<=games<=82 and games.is_integer()) else ''
        seen.add(id)
        if reason:
            rejected.append((ix,reason));reasons[reason]=reasons.get(reason,0)+1
            continue
        values={key:number(row[key]) for key in ['points_per_game','minutes_per_game']}
        for key,upper in [('points_per_game',float('inf')),('minutes_per_game',48)]:
            if values[key] is not None and not 0<=values[key]<=upper:
                values[key]=None
        eligible.append({'source_row':ix,'player_id':id,'team':team,'position':position,'games_played':games,**values})
    expected=copy.deepcopy(eligible);imputed={}
    for key in ['points_per_game','minutes_per_game']:
        values=[r[key] for r in eligible if r[key] is not None]
        fallback=statistics.median(values) if values else 0
        imputed[key]=sum(r[key] is None for r in eligible)
        for row in expected:
            if row[key] is None:
                group=[r[key] for r in eligible if r['position']==row['position'] and r[key] is not None]
                row[key]=statistics.median(group) if group else fallback
            row['total_points']=row['games_played']*row['points_per_game']
    actual=pd.read_csv(out/'recovered.csv').sort_values('player_id').reset_index(drop=True)
    expected_frame=pd.DataFrame(sorted(expected,key=lambda row:row['player_id']),columns=actual.columns)
    assert_frame_equal(actual,expected_frame,check_dtype=False,atol=1e-6,rtol=1e-6)
    actual_rejected=pd.read_csv(out/'rejected.csv')
    assert list(zip(actual_rejected.source_row,actual_rejected.reason))==rejected
    report=load(out/'quality_report.json')
    assert report['input_rows']==len(rows) and report['rejected_rows']==len(rejected)
    assert report['eligible_rows']==report['players']==len(eligible)
    assert report['imputed_cells']==imputed and report['rejection_counts']==reasons
    counts={}
    for row in expected:counts[row['team']]=counts.get(row['team'],0)+1
    assert report['players_per_team']==counts
    close(report['total_points'],sum(row['total_points'] for row in expected))


def check_geo(data,out):
    rows=list(csv.DictReader((data/'data.csv').open()));seen=set();expected=[]
    for row in rows:
        id=row['trip_id'].strip();route=row['route'].strip();duplicate=id in seen;seen.add(id)
        fields=['origin_lat','origin_lon','dest_lat','dest_lon','distance_km','passengers','delay_minutes']
        v={key:number(row[key]) for key in fields}
        if not id or not route or duplicate or any(x is None for x in v.values()):continue
        if not all(-90<=v[key]<=90 for key in ['origin_lat','dest_lat']):continue
        if not all(-180<=v[key]<=180 for key in ['origin_lon','dest_lon']):continue
        if not all(v[key]>=0 for key in ['distance_km','passengers','delay_minutes']) or not v['passengers'].is_integer():continue
        lat1,lon1,lat2,lon2=map(math.radians,[v[key] for key in fields[:4]])
        h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
        h=min(1,max(0,h));km=2*6371.0088*math.atan2(math.sqrt(h),math.sqrt(1-h))
        expected.append({'trip_id':id,'route':route,'km':km,'pkm':v['distance_km']*v['passengers'],'delay':v['delay_minutes'],'ratio':v['distance_km']/km if km else None})
    actual=pd.read_csv(out/'trip_metrics.csv').set_index('trip_id')
    assert set(actual.index)=={r['trip_id'] for r in expected}
    for r in expected:
        a=actual.loc[r['trip_id']];close(a.great_circle_km,r['km']);close(a.passenger_km,r['pkm'])
        assert pd.isna(a.detour_ratio) if r['ratio'] is None else math.isclose(a.detour_ratio,r['ratio'],abs_tol=1e-6,rel_tol=1e-6)
    grouped={}
    for r in expected:grouped.setdefault(r['route'],[]).append(r)
    routes=pd.read_csv(out/'route_summary.csv').set_index('route')
    assert set(routes.index)==set(grouped)
    for name,group in grouped.items():
        row=routes.loc[name];assert row.trip_count==len(group)
        close(row.mean_great_circle_km,statistics.mean(r['km'] for r in group))
        close(row.total_passenger_km,sum(r['pkm'] for r in group));close(row.mean_delay_minutes,statistics.mean(r['delay'] for r in group))
    report=load(out/'spatial_report.json')
    assert report['quality']=={'input_rows':len(rows),'valid_rows':len(expected),'rejected_rows':len(rows)-len(expected)}
    assert report['route_count']==len(grouped)
    assert report['top_routes']==sorted(grouped,key=lambda key:(-len(grouped[key]),key))[:5]
    close(report['total_passenger_km'],sum(r['pkm'] for r in expected))
    if expected:close(report['mean_great_circle_km'],statistics.mean(r['km'] for r in expected))
    else:assert report['mean_great_circle_km'] is None


def check_energy(data,out):
    hourly=pd.read_csv(data/'energy_consumption.csv',parse_dates=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    weather=pd.read_csv(data/'weather.csv',parse_dates=['date']).set_index('date')
    values=[]
    for i in range(24,len(hourly)):
        r=hourly.iloc[i];previous=r.timestamp.normalize()-pd.Timedelta(days=1)
        if previous not in weather.index:continue
        w=weather.loc[previous]
        values.append([r.timestamp,r.consumption_kwh,hourly.iloc[i-24].consumption_kwh,r.timestamp.hour,r.timestamp.dayofweek,r.timestamp.month,r.is_holiday,w.temp_avg,w.humidity_avg,w.cloud_cover_avg,w.wind_avg])
    expected=pd.DataFrame(values,columns=['timestamp','consumption_kwh',*FEATURES])
    features=pd.read_csv(out/'features.csv',parse_dates=['timestamp'])
    assert_frame_equal(features,expected,check_dtype=False,rtol=1e-6,atol=1e-6)
    cut=math.floor(0.8*len(expected));train=expected.iloc[:cut];test=expected.iloc[cut:]
    for name,frame in [('train',train),('test',test)]:
        actual=pd.read_csv(out/(name+'.csv'),parse_dates=['timestamp'])
        assert_frame_equal(actual,frame.reset_index(drop=True),check_dtype=False,rtol=1e-6,atol=1e-6)
    X=train[FEATURES].to_numpy(float);y=train.consumption_kwh.to_numpy(float)
    mean=X.mean(axis=0);scale=X.std(axis=0,ddof=0);scale[scale==0]=1
    scaled=(X-mean)/scale
    # Independent closed-form solution to Ridge's specified least-squares objective.
    coefficients=np.linalg.solve(scaled.T@scaled+np.eye(len(FEATURES)),scaled.T@(y-y.mean()))
    prediction=(test[FEATURES].to_numpy(float)-mean)/scale@coefficients+y.mean()
    actual=pd.read_csv(out/'predictions.csv',parse_dates=['timestamp'])
    assert actual.timestamp.tolist()==test.timestamp.tolist()
    np.testing.assert_allclose(actual.actual_kwh,test.consumption_kwh,atol=1e-6,rtol=1e-6)
    np.testing.assert_allclose(actual.predicted_kwh,prediction,atol=1e-6,rtol=1e-6)
    # This pickle is produced by the trusted local reference, never untrusted generated code.
    with (out/'model.pkl').open('rb') as handle:
        model=pickle.load(handle)
    np.testing.assert_allclose(model.predict(test[FEATURES]),prediction,atol=1e-6,rtol=1e-6)
    metadata=load(out/'fit_metadata.json')
    assert metadata['train_rows']==len(train) and metadata['test_rows']==len(test) and metadata['features']==FEATURES
    np.testing.assert_allclose(metadata['scaler_mean'],mean,atol=1e-6,rtol=1e-6)
    np.testing.assert_allclose(metadata['scaler_scale'],scale,atol=1e-6,rtol=1e-6)
    error=test.consumption_kwh.to_numpy()-prediction
    result=load(out/'energy_report.json');close(result['mae_kwh'],np.abs(error).mean());close(result['rmse_kwh'],np.sqrt((error**2).mean()))
    assert result==load(out/'metrics.json')


CHECKERS={S:check_sports,G:check_geo,E:check_energy}

def run(name,data,out,expect_failure=False):
    out.mkdir()
    result=subprocess.run([sys.executable,str(ROOT/'pipelines'/name/'reference.py'),'--data-dir',str(data),'--output-dir',str(out)],capture_output=True,text=True)
    if expect_failure:
        assert result.returncode!=0, 'Invalid source was accepted'
        return
    if result.returncode:raise RuntimeError(result.stderr)
    graph=load(ROOT/'pipelines'/name/'task_graph.json')
    for artifact in graph['artifacts']:
        file=out/artifact['path'];assert file.is_file(), file
        if file.suffix=='.csv':assert set(artifact['required_columns'])<=set(pd.read_csv(file,nrows=0))
        if file.suffix=='.json':load(file)
    CHECKERS[name](data,out)


def main():
    results=[]
    with tempfile.TemporaryDirectory(prefix='inlumen-pilot-') as temp:
        temp=Path(temp)
        for name in [S,G,E]:
            source=ROOT/'pipelines'/name;graph=load(source/'task_graph.json')
            validate(graph,source)
            out=temp/name;run(name,source/'inputs',out)
            results.append({'case':name,'probe':'revised_visible_fixture','status':'passed','output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}})
        sports=temp/'sports-probe';sports.mkdir()
        pd.DataFrame([
            ['A',' X ','Guard',10,None,None],['B','X','Guard',12,None,None],['C','Y','Center',8,None,None],
            ['D','Y','Center',-1,2,20],['D','Y','Center',10,3,30],['','Z','Guard',-2,4,40],
        ],columns=['player_id','team','position','games_played','points_per_game','minutes_per_game']).to_csv(sports/'data.csv',index=False)
        run(S,sports,temp/'sports-probe-out');results.append({'case':S,'probe':'all_missing_zero_fallback_and_rejection_priority','status':'passed'})
        geo=temp/'geo-probe';geo.mkdir()
        columns=['trip_id','route','origin_lat','origin_lon','dest_lat','dest_lon','distance_km','passengers','delay_minutes']
        pd.DataFrame([
            ['A','Z',0,0,0,0,0,2,0],['B','A',0,0,0,180,20000,3,4],['C','X',91,0,0,0,1,1,0],
            ['D','A',0,0,0,90,10000,1,2],['E','Z',0,0,0,1,100,1,0],
        ],columns=columns).to_csv(geo/'data.csv',index=False)
        run(G,geo,temp/'geo-probe-out');results.append({'case':G,'probe':'zero_distance_antipodes_invalid_latitude_and_rank_tie','status':'passed'})
        pd.DataFrame([['C','X',91,0,0,0,1,1,0]],columns=columns).to_csv(geo/'data.csv',index=False)
        run(G,geo,temp/'geo-empty-out');results.append({'case':G,'probe':'empty_valid_partition','status':'passed'})
        energy=temp/'energy-probe';energy.mkdir()
        original=ROOT/'pipelines'/E/'inputs'
        hourly=pd.read_csv(original/'energy_consumption.csv').head(96)
        weather=pd.read_csv(original/'weather.csv').head(4)
        weather.loc[1,'temp_avg']+=50
        hourly.iloc[::-1].to_csv(energy/'energy_consumption.csv',index=False)
        weather.iloc[::-1].to_csv(energy/'weather.csv',index=False)
        run(E,energy,temp/'energy-probe-out');results.append({'case':E,'probe':'shuffled_inputs_lagged_weather_train_only_scaling_closed_form_prediction','status':'passed'})
        hourly.drop(index=25).to_csv(energy/'energy_consumption.csv',index=False)
        run(E,energy,temp/'energy-gap-out',expect_failure=True);results.append({'case':E,'probe':'missing_hour_rejected','status':'passed'})
        hourly.to_csv(energy/'energy_consumption.csv',index=False)
        pd.concat([weather,weather.iloc[[0]]]).to_csv(energy/'weather.csv',index=False)
        run(E,energy,temp/'energy-duplicate-out',expect_failure=True);results.append({'case':E,'probe':'duplicate_weather_date_rejected','status':'passed'})
        graph=load(ROOT/'pipelines'/S/'task_graph.json');bad=copy.deepcopy(graph);bad['dependencies'].pop()
        try:validate(bad)
        except AssertionError:pass
        else:raise AssertionError('Missing data dependency accepted')
        results.append({'case':'schema','probe':'missing_artifact_dependency_rejected','status':'passed'})
        for name in [S,G,E]:
            for track in ['natural_language','fixed_graph']:
                dest=export(name,temp/(name+'-'+track),track)
                files={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
                assert not any(Path(p).name in {'reference.py','task_graph.json','provenance.json','requirements.txt'} for p in files)
                assert ('provided_graph.json' in files)==(track=='fixed_graph')
        results.append({'case':'export','probe':'generator_input_allowlist_both_tracks','status':'passed'})
    report={'status':'passed','scope':'Python references, independent behavioral calculations, graph consistency, and export allowlists; not Dagster execution or generated-code evaluation',
            'dagster_runtime_qualification':'not_run','review_status':'author_review_pending','python':sys.version.split()[0],
            'packages':{name:version(name) for name in ['pandas','numpy','scipy','scikit-learn','jsonschema']},'checks':results}
    (ROOT/'qualification-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':'passed','check_groups':len(results),'dagster_runtime_qualification':'not_run'},indent=2))

if __name__=='__main__':main()
