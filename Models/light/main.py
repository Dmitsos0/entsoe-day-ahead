import lightgbm
import pandas as pd
from PythonFiles.Tools.files import get_data_path,get_project_dir
from dotenv import load_dotenv
from pathlib import Path
import time
import os
import matplotlib.pyplot as plt
DATA_DIR = get_data_path() 
PROJECT_DIR = get_project_dir()

MODELS_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = MODELS_DIR / "Outputs"
WEIGHTS_DIR = MODELS_DIR / "Weights"
MODEL_NAME = "Lightgbm"

MODEL_DIR = WEIGHTS_DIR / f"{MODEL_NAME}.txt" 
def train_model():
    load_dotenv()
    train_start = pd.Timestamp(os.getenv("START_DATE_TRAINING"), tz="UTC")
    train_end = pd.Timestamp(os.getenv("END_DATE_TRAINING"), tz="UTC")  
    frames: list[pd.DataFrame] = []
    for folder in Path(DATA_DIR).iterdir():
        if folder.is_dir():

            for file in folder.iterdir():
                if file.is_dir() or file.suffix != ".parquet": continue
                df = pd.read_parquet(file)
                df["timestamp"] = pd.to_datetime(df["timestamp"],utc=True)
                df = df.set_index("timestamp").sort_index()
                df = df[~df.index.duplicated(keep="first")]
                df.columns = df.columns.str.strip()
                frames.append(df)
                
    merged :pd.DataFrame = pd.concat(frames,axis=1,join="outer",sort = True)
    merged = merged.reindex(pd.date_range(merged.index.min(), merged.index.max(), freq="h", tz="UTC"))
    merged["VWAP"] = merged["VWAP"].ffill()
    merged = merged[(merged.index >= train_start) & (merged.index < train_end + pd.Timedelta(days=1))]

    merged["price_lag_24h"] = merged["actual_price"].shift(24)
    merged["price_lag_168h"] = merged["actual_price"].shift(168)

    local = merged.index.tz_convert("Europe/Athens")

    merged["hour"] = local.hour
    merged["day"] = local.weekday
    merged["month"] = local.month
    merged = merged.dropna(subset=["actual_price", "price_lag_24h", "price_lag_168h"])
    price_col = 'actual_price' 
    feature_cols = ["production_forecast", "load_forecast", "hour", "day", "month", "price_lag_24h","price_lag_168h","solar_forecast","wind_forecast","VWAP"]

    X = merged[feature_cols]
    y = merged[price_col]
    print(merged.index.to_series().diff().value_counts().head())



    dataset = lightgbm.Dataset(X, label=y)
    params = {
        'objective':'quantile',
        'alpha' : 0.50,
        'metric':'quantile',
        'learning_rate': 0.012,
        'num_leaves' : 10,
        'verbose' : -1,
        'min_child_samples':200,
        'lambda_l2': 1,


    }
    model = lightgbm.train(
        params,
        dataset,
        num_boost_round=1000,
        )   
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    model.save_model(MODEL_DIR)
def test_model():
    model = lightgbm.Booster(model_file=MODEL_DIR)

    load_dotenv()
    test_start = pd.Timestamp(os.getenv("START_DATE_TESTING"), tz="UTC")
    test_end = pd.Timestamp(os.getenv("END_DATE_TESTING"), tz="UTC")  
    frames: list[pd.DataFrame] = []
    for folder in Path(DATA_DIR).iterdir():
        if folder.is_dir():

            for file in folder.iterdir():
                if file.is_dir() or file.suffix != ".parquet": continue
                df = pd.read_parquet(file)
                df["timestamp"] = pd.to_datetime(df["timestamp"],utc=True)
                df = df.set_index("timestamp").sort_index()
                df = df[~df.index.duplicated(keep="first")]
                df.columns = df.columns.str.strip()
                frames.append(df)
    merged :pd.DataFrame = pd.concat(frames,axis=1,join="outer",sort = True)
    merged = merged.sort_index()
    merged = merged.reindex(pd.date_range(merged.index.min(), merged.index.max(), freq="h", tz="UTC"))
    merged["VWAP"] = merged["VWAP"].ffill()
    merged = merged[(merged.index >= test_start) & (merged.index < test_end + pd.Timedelta(days=1))]

    merged["price_lag_24h"] = merged["actual_price"].shift(24)
    merged["price_lag_168h"] = merged["actual_price"].shift(168)

    local = merged.index.tz_convert("Europe/Athens")

    merged["hour"] = local.hour
    merged["day"] = local.weekday
    merged["month"] = local.month
    merged = merged.dropna(subset=["actual_price", "price_lag_24h", "price_lag_168h"])
    price_col = 'actual_price' 
    feature_cols = ["production_forecast", "load_forecast", "hour", "day", "month", "price_lag_24h","price_lag_168h","solar_forecast","wind_forecast","VWAP"]

    testDf = merged[feature_cols]
    expectedDf = merged[price_col].to_frame()


    prediction = model.predict(testDf)

    expectedDf["hour"] = testDf["hour"]
    expectedDf["output"] = prediction
    expectedDf["error"] = (expectedDf["output"] - expectedDf[price_col]).abs()
    expectedDf["load_forecast"] = testDf["load_forecast"]
    expectedDf["production_forecast"] = testDf["production_forecast"]
    expectedDf["solar_forecast"] = testDf["solar_forecast"]

    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    expectedDf.to_parquet(OUTPUT_DIR / f"{MODEL_NAME}.parquet")


    total_error = expectedDf["error"].sum()
    total_price = expectedDf[price_col].abs().sum()
    error = ((total_error)/total_price) * 100   
    print(error)
    draw_graph(expectedDf,error)


def draw_graph(df: pd.DataFrame,error : float):
    daily = df[["output", "actual_price"]].resample("D").mean().dropna()

    ax = daily.plot(y=["output", "actual_price"], kind="line")
    ax.set_title(f"Price prediction vs Actual, WAPE:{error:.2f}%")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.grid(True, linestyle="--", alpha=0.6)

    plt.savefig(PROJECT_DIR / "chart.png", dpi=300, bbox_inches="tight")
    plt.close()

    
if(__name__ == "__main__"):
    train_model()
    time.sleep(2)
    test_model()