"""Batch 09 references, reusing qualified batch-08 primitives for matching behaviors."""
import argparse,json,pickle,sys
from pathlib import Path
import numpy as np,pandas as pd
from sklearn.linear_model import LinearRegression,LogisticRegression
from sklearn.metrics import accuracy_score,f1_score,mean_absolute_error,mean_squared_error,precision_score,recall_score,roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
TOOLS=Path(__file__).resolve().parents[2]/'tools';sys.path.insert(0,str(TOOLS))
from batch08_reference import ranking,fanin,fanout,route_fanout,prep,js
def dual(data,out):
 d=pd.read_csv(data/'data.csv');reg=['games_played','points_per_game','assists_per_game','rebounds_per_game','minutes_per_game','age','experience_years','salary_millions','injury_games_missed','win_shares','field_goal_pct','three_point_pct','free_throw_pct'];cls=[*reg,'market_value','contract_year'];cols=['player_id','all_star','market_value',*set(reg+cls)];prep(d,cols,'player_id')
 rd=d[['player_id','market_value',*reg]].sort_values('player_id');rd.to_csv(out/'regression_data.csv',index=False);tr,te=train_test_split(rd,test_size=.2,random_state=42);rm=Pipeline([('scale',StandardScaler()),('model',LinearRegression())]);rm.fit(tr[reg],tr.market_value);rp=rm.predict(te[reg]);
 with (out/'market_model.pkl').open('wb') as h:pickle.dump(rm,h)
 pd.DataFrame({'player_id':te.player_id,'actual_market_value':te.market_value,'predicted_market_value':rp}).sort_values('player_id').to_csv(out/'market_predictions.csv',index=False);js(out/'market_metrics.json',{'train_rows':len(tr),'test_rows':len(te),'mae':mean_absolute_error(te.market_value,rp),'rmse':mean_squared_error(te.market_value,rp)**.5,'r2':rm.score(te[reg],te.market_value)})
 cd=d[['player_id','all_star',*cls]].sort_values('player_id');cd.to_csv(out/'classification_data.csv',index=False);tr,te=train_test_split(cd,test_size=.25,random_state=42,stratify=cd.all_star);cm=Pipeline([('scale',StandardScaler()),('model',LogisticRegression(C=1,solver='liblinear',max_iter=1000,random_state=42))]);cm.fit(tr[cls],tr.all_star);prob=cm.predict_proba(te[cls])[:,1];yp=(prob>=.5).astype(int)
 with (out/'allstar_model.pkl').open('wb') as h:pickle.dump(cm,h)
 pd.DataFrame({'player_id':te.player_id,'actual_all_star':te.all_star,'probability':prob,'predicted_all_star':yp}).sort_values('player_id').to_csv(out/'allstar_predictions.csv',index=False);js(out/'allstar_metrics.json',{'train_rows':len(tr),'test_rows':len(te),'accuracy':accuracy_score(te.all_star,yp),'precision':precision_score(te.all_star,yp,zero_division=0),'recall':recall_score(te.all_star,yp,zero_division=0),'f1':f1_score(te.all_star,yp,zero_division=0),'roc_auc':roc_auc_score(te.all_star,prob)})
RUNNERS={'024_sports_regression_prediction_statistical':dual,'033_sports_statistical_cleaning_integration_v3':ranking,'039_sports_statistical_visualization_cleaning':fanin,'059_transportation_cleaning_integration_recovery':fanout,'088_transportation_statistical_integration_v2':route_fanout}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
