import pandas as pd
from PythonFiles.Tools.files import get_data_path,get_models_dir
from PythonFiles.Tools.Dates import get_dates
import os
from dotenv import load_dotenv

MODELS_DIR = get_models_dir()
OUTPUTS_DIR = MODELS_DIR / "Outputs"
DATA_DIR = get_data_path()
PRICES_DIR = DATA_DIR / "entsoe/actual_price.parquet"
def test_naive():
    load_dotenv()
    test_start = pd.Timestamp(os.getenv("START_DATE_TESTING"),tz="UTC")
    test_end = pd.Timestamp(os.getenv("END_DATE_TESTING"),tz="UTC")
    prices = pd.read_parquet(PRICES_DIR)
    prices["price_lag_168h"] = prices["actual_price"].shift(168)
    prices = prices.dropna()
    prices = prices.set_index("timestamp")
    prices = prices[(prices.index >= test_start) & (prices.index < test_end + pd.Timedelta(days=1))]
    print(prices.head(),prices.tail())
    errors = (prices["actual_price"] - prices["price_lag_168h"]).abs()
    wape = errors.sum()/prices["actual_price"].sum() * 100 
    mae = errors.mean()
    print("WAPE: ",wape,"%")
    print("MAE:",mae)

    prices = prices.rename(columns={"price_lag_168h":"prediction"})

    output = OUTPUTS_DIR / "naive.parquet"
    prices.to_parquet(output)
test_naive()