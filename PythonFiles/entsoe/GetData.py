import os
import pandas as pd
from pathlib import Path
from entsoe import EntsoePandasClient
from PythonFiles.Tools.Dates import get_dates
from PythonFiles.Tools.files import load_env,get_data_path

starts_at,ends_at = get_dates()
print("start: ",starts_at," end: ",ends_at)
load_env()
DATA_DIR = get_data_path()
PATH = DATA_DIR / "entsoe" 

if(not PATH.is_dir):
    PATH.mkdir(parents=True,exist_ok=True)


client = EntsoePandasClient(os.getenv("ENTSOE_API_KEY"))
def get_load_forecast():
    df = client.query_load(country_code="GR",start=starts_at,end=ends_at)
    
    df.index = df.index.tz_convert("UTC")
    if isinstance(df, pd.Series):
        df = df.to_frame(name="load_forecast")
    else:
        df = df.rename({"Actual Load" : "load_forecast"},axis=1)

    df = df[~df.index.duplicated(keep="last")] 
    df = df.resample("h").mean().dropna()

    df = df.rename_axis("timestamp").reset_index()
    fPATH = PATH / "load_forecast.parquet"
    print(fPATH)

    df.to_parquet(fPATH,index=False)

def get_solar_production_forecast():
    df = client.query_wind_and_solar_forecast(country_code="GR",start=starts_at,end=ends_at,psr_type="B16")

    df.index = df.index.tz_convert("UTC")
    if isinstance(df, pd.Series):
        df = df.to_frame(name="solar_forecast")
    else:
        df = df.rename({"Solar" : "solar_forecast"},axis=1)
    df = df[~df.index.duplicated(keep="last")] 
    df = df.resample("h").mean().dropna()

    df = df.rename_axis("timestamp").reset_index()
    fPATH = PATH / "solar_forecast.parquet"
    print(fPATH)
    df.to_parquet(fPATH,index=False)


def get_wind_production_forecast():
    df = client.query_wind_and_solar_forecast(country_code="GR",start=starts_at,end=ends_at,psr_type="B19")
    df.index = df.index.tz_convert("UTC")
    if isinstance(df, pd.Series):
        df = df.to_frame(name="wind_forecast")
    else:
        df = df.rename({"Wind Onshore":"wind_forecast"},axis=1)
    df = df[~df.index.duplicated(keep="last")] 
    df = df.resample("h").mean().dropna()

    df = df.rename_axis("timestamp").reset_index()

    fPATH = PATH / "wind_forecast.parquet"
    print(fPATH)
    df.to_parquet(fPATH,index=False)

def get_energy_production_forecast():
    df = client.query_generation_forecast(country_code="GR",start=starts_at,end=ends_at)
    df.index = df.index.tz_convert("UTC")
    if isinstance(df, pd.Series):
        df = df.to_frame(name="production_forecast")
    df = df[~df.index.duplicated(keep="last")] 
    df = df.resample("h").mean().dropna()
    df = df.rename_axis("timestamp").reset_index()

    fPATH = PATH / "energy_production_forecast.parquet"
    print(fPATH)
    df.to_parquet(fPATH,index=False)

def get_energy_price():
    df = client.query_day_ahead_prices(country_code="GR",start=starts_at,end=ends_at)
    df.index = df.index.tz_convert("UTC")
    if isinstance(df, pd.Series):
        df = df.to_frame(name="actual_price")
    df = df[~df.index.duplicated(keep="last")] 
    df = df.resample("h").mean().dropna()
    df = df.rename_axis("timestamp").reset_index()
    
    fPATH = PATH / "energy_price.parquet"
    print(fPATH)
    df.to_parquet(fPATH,index=False)


def get_all_entsoe():
    get_energy_price()
    get_energy_production_forecast()
    get_wind_production_forecast()
    get_solar_production_forecast()
    get_load_forecast()

