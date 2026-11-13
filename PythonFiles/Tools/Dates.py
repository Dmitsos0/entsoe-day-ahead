from pandas import Timestamp
from os import getenv
from PythonFiles.Tools.files import load_env
import sys
from pathlib import Path
import pandas as pd
def get_dates() -> tuple[Timestamp,Timestamp]:
    load_env()
    start1 = Timestamp(getenv("START_DATE_TRAINING"),tz="UTC")
    start2 = Timestamp(getenv("START_DATE_TESTING"),tz="UTC")
    end1 = Timestamp(getenv("END_DATE_TRAINING"),tz="UTC")
    end2 = Timestamp(getenv("END_DATE_TESTING"),tz="UTC")
    if(not start1):
        print("You have not specified a start time for training read the README for more instructions")
    if(not start2):
        print("You have not specified a start time for testing read the README for more instructions")
    if(not end1):
        print("You have not specified an end time for training read the README for more instructions")
    if(not end2):
        print("You have not specified an end time for testing read the README for more instructions")

    if((not start1) or (not start2) or (not end1) or (not end2)): sys.exit()
    start = min(start1,start2)
    end = max(end1,end2)

    return (start,end)



    