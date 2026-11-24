from PythonFiles.Tools.files import get_pythonfiles_path,get_models_dir
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
DATA = get_pythonfiles_path() / ("EnexGas/Resources")
PARENT = Path(__file__).parent

SAVE_DIR = PARENT / "GasAnalysis"

MODEL_DIR = get_models_dir()
MODEL_OUTPUTS = MODEL_DIR / "Outputs"
def draw_enex_gas_price_graphs():
    prices = pd.read_parquet((MODEL_OUTPUTS / "Lightgbm.parquet"))
    prices.resample("D").mean().dropna()
    print(prices.columns)
    for yearFolder in DATA.iterdir():
        dataframes : list[pd.DataFrame] = []
        for file in yearFolder.iterdir():
            frame = pd.read_excel(file)
            timestamp = pd.to_datetime(file.name.split("_")[0]).tz_localize("UTC")
            timestamp = timestamp + pd.Timedelta(days=1)
            frame = frame[~frame["Contract"].isin(["WD","D+2","D+3","WE"])]
            frame = frame[["VWAP ","HGSIDA"]]
            frame["timestamp"] = timestamp
            frame["actual_price"] = frame["timestamp"].map(prices["actual_price"])
            frame["predicted_price"] = frame["timestamp"].map(prices["output"])
            dataframes.append(frame)

        df = pd.concat(dataframes)
        df = df.set_index("timestamp").sort_index()

        ax = df.plot(y=["VWAP ","HGSIDA","actual_price","predicted_price"],kind="line")
        ax.set_title("VWAP vs HGSIDA vs Actual Energy Price vs Predicted price")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.grid(True,alpha=0.6,linestyle="--")

        SAVE_DIR.mkdir(parents=True,exist_ok=True)
        plt.savefig(SAVE_DIR / f"{yearFolder.stem}.png",dpi=300,bbox_inches="tight")
        plt.close()

draw_enex_gas_price_graphs()