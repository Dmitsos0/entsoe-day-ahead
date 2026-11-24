from pandas import Timestamp
from os import getenv
from PythonFiles.Tools.files import load_env
import sys
from pathlib import Path
import pandas as pd
from bisect import bisect_left
from pandas.tseries.frequencies import to_offset

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

def check_is_greater(freq1: str, freq2: str) -> bool:
    ref_date = pd.Timestamp("2026-01-01")
    return (ref_date + pd.tseries.frequencies.to_offset(freq1) > ref_date + pd.tseries.frequencies.to_offset(freq2))


def get_missing(directory: Path, start: pd.Timestamp, end: pd.Timestamp, frequency: str = "D",name = "*",extension: str = "*",column: str = "timestamp") -> list[tuple[pd.Timestamp,pd.Timestamp]]:
    """
    
    Parameters:

    directory: The directory which contains data with files who contain time data

    start: The first point in the search
    end: The last point

    frequency: How many files should appear over a time period e.g hourly 
    means there should be 24 files in a day. it accepts frequency strings
    from pandas' timeseries.offset_aliases

    name: the name of the file(s) leaving it default will check all files
    extension: search for files ending only in a certain extension. the default accepted are
    .json, .xlsx, .parquet, .csv

    column: the column which will contain the time date of the document

    Returns:
    A list that contains tuples of missing time ranges, where the first index is the start of when the range is missing and the last is the end
    (inclusive)

    """
    load_env()
    GLOBAL_CUTOFF = pd.Timestamp(getenv("GLOBAL_CUTOFF"))
    final = f"{name}.{extension}"

    existing: list[pd.Timestamp] = []
    for p in directory.rglob(final):
        if p.is_file():
            df = pd.DataFrame()
            if p.suffix.lower() == ".csv":
                df = pd.read_csv(p,usecols=[column])
            elif p.suffix.lower() == ".json":
                df = pd.read_json(p)
            elif p.suffix.lower() == ".parquet":
                df = pd.read_parquet(p,columns=[column])
            elif p.suffix.lower() == ".xlsx":
                df = pd.read_excel(p,usecols=[column])
            else: continue

            existing.extend(pd.to_datetime(df[column],utc=True))
    
    existing.sort()     
    missing: list[tuple[pd.Timestamp,pd.Timestamp]] = []
    prev_exists = True

    end = end + pd.Timedelta(days=1) - to_offset(frequency)
    for interval in pd.date_range(start,end,freq=frequency,tz="UTC"):
        index = bisect_left(existing,interval)
        found = index < len(existing) and existing[index] == interval
        if(not found):
            if(prev_exists):
                missing.append((interval,interval))
            else:
                last = missing.pop()[0]
                timestamp_range = (last,interval)
                missing.append(timestamp_range)
        prev_exists= found

    if(len(missing) == 0): print("Nothing missing in the date range provided!")
    return missing #returns a sorted list of missing ranges with Timestamps or an empty list if nothing is missing


def get_missing_years(missing:list[tuple[pd.Timestamp]]) -> list[int]:
    """
    Given a list of missing ranges as Timestamp tuples it will return a list of missing years as Timestamps
    """
    missing_years: set[pd.Timestamp] = set()

    for missing_range in missing:
        starts_at = missing_range[0].year
        ends_at = missing_range[1].year
        while(starts_at <= ends_at):
            missing_years.add(starts_at)
            starts_at+=1


    res: list[int] = []
    for year in missing_years:
        res.append(year)

    return res

