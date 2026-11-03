import pandas as pd
import numpy as np
import json as json
from sklearn.model_selection._split import train_test_split as train_test_split
from sklearn.pipeline import Pipeline as Pipeline
from sklearn.compose._column_transformer import ColumnTransformer as ColumnTransformer
from sklearn.preprocessing._data import StandardScaler as StandardScaler
from sklearn.preprocessing._encoders import OneHotEncoder as OneHotEncoder
from sklearn.linear_model._logistic import LogisticRegression as LogisticRegression
import pickle as pickle
from sklearn.metrics._classification import accuracy_score as accuracy_score
from sklearn.metrics._classification import precision_score as precision_score
from sklearn.metrics._classification import recall_score as recall_score
from sklearn.metrics._classification import f1_score as f1_score
from sklearn.metrics._ranking import roc_auc_score as roc_auc_score
def js(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+"\n")

