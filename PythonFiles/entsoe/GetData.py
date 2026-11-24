import os
import pandas as pd
from pathlib import Path
from entsoe import EntsoePandasClient
from PythonFiles.Tools.Dates import get_dates,get_missing
from PythonFiles.Tools.files import load_env,get_data_path
from entsoe.exceptions import NoMatchingDataError
from requests.exceptions import HTTPError
from typing import Callable, Optional
import time
import json
starts_at,ends_at = get_dates()
print("start: ",starts_at," end: ",ends_at)
load_env()
DATA_DIR = get_data_path()
PATH = DATA_DIR / "entsoe" 

if(not PATH.is_dir()):
    PATH.mkdir(parents=True,exist_ok=True)


client = EntsoePandasClient(os.getenv("ENTSOE_API_KEY"))


def fetch(fn: Callable,
          start: pd.Timestamp,
          end: pd.Timestamp,psr_type: Optional[str] = None,
          country_code:str = "GR",
          retries: int = 4) -> tuple[pd.DataFrame,list[tuple[pd.Timestamp,pd.Timestamp]]]:
    noData: list[tuple[pd.Timestamp,pd.Timestamp]] = []

    params = dict()
    if(psr_type is not None):
        params["psr_type"] = psr_type
    params["country_code"] = country_code
    params["start"] = start
    params["end"] = end + pd.Timedelta(hours=1)

    for attempt in range(retries):
        try:
            return (fn(**params),[])
        except HTTPError as e:
            wait = 3 * 2 ** attempt
            print(f"{type(e).__name__} on {start} -> {end}, retry {attempt + 1}/{retries} in {wait}s")
            time.sleep(wait)
        except NoMatchingDataError as e:
            print(f"No data for the timestamps {start} -> {end}")
            noData.append((params["start"],params["end"]))
            return (None,noData)
    print(f"giving up on the range {start} -> {end}")
    return (None,[])

def check_existing(fname: str) -> list[tuple[pd.Timestamp,pd.Timestamp]]:
    return get_missing(directory=PATH,start=starts_at,end=ends_at,name=fname,frequency="h")


def update_dataset(name:str,query: Callable,psr_type: Optional[str] = None):
    print(f"getting {name} data...")

    path = PATH / f"{name}.parquet"
    dataframes: list[pd.DataFrame] = []

    noData:tuple[pd.Timestamp,pd.Timestamp] = []

    missing = check_existing(fname=name)
    for s,e in missing:
        df,n = fetch(query,start=s,end=e,psr_type=psr_type)
        noData.extend(n)

        if(df is None): continue
        if isinstance(df, pd.DataFrame):
            if df.shape[1] != 1:
                raise ValueError(f"{name}: expected 1 column, got {list(df.columns)}")
            df = df.iloc[:, 0]
        df = df.rename(name)

        df.index = df.index.tz_convert("UTC")
        df = df[~df.index.duplicated(keep="last")]
        df = df.resample("h").mean().dropna()
        dataframes.append(df.rename_axis("timestamp").reset_index())

    if not dataframes:
        return                                     # nothing new, leave the file alone

    frames = ([pd.read_parquet(path)] if path.exists() else []) + dataframes
    res = (pd.concat(frames)
             .drop_duplicates("timestamp", keep="last")
             .sort_values("timestamp"))
    res.to_parquet(path, index=False)



def get_all_entsoe():
    update_dataset("actual_price",client.query_day_ahead_prices)
    update_dataset("production_forecast", client.query_generation_forecast)
    update_dataset("wind_forecast", client.query_wind_and_solar_forecast, psr_type="B19")
    update_dataset("solar_forecast", client.query_wind_and_solar_forecast, psr_type="B16")
    update_dataset("load_forecast", client.query_load_forecast)
