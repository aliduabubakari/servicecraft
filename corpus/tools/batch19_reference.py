"""Executable behavioral references for batch 19."""
import argparse,sys
from pathlib import Path
TOOLS=Path(__file__).resolve().parents[2]/'tools';sys.path.insert(0,str(TOOLS))
from batch11_reference import prediction_parallel
from batch16_reference import sports_multiview,position_linear,trip_fanout
from batch17_reference import operations_fanin
RUNNERS={'041_sports_statistical_visualization_integration':sports_multiview,'051_sports_visualization_integration_validation':position_linear,'075_transportation_prediction_validation_v2':prediction_parallel,'093_transportation_visualization_cleaning_validation':trip_fanout,'097_transportation_visualization_integration_v2':operations_fanin}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);x=p.parse_args();x.output_dir.mkdir(parents=True,exist_ok=True);RUNNERS[Path(__file__).resolve().parent.name](x.data_dir,x.output_dir)
