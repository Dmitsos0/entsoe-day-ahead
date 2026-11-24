from PythonFiles.Tools.files import get_models_dir
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
MODEL_DIR = get_models_dir()
OUTPUTS_DIR = MODEL_DIR / "Outputs"

def analyze_lightgbm(frequency: str = "h",ax: Axes = None)->Axes:
    FILE_DIR = OUTPUTS_DIR / "lightgbm.parquet"
    df = pd.read_parquet(FILE_DIR)
    df = df.resample(frequency).mean().dropna()

    ax = df.plot(y=["actual_price","predicted_price"],kind="line",ax=ax)

    return ax

def analyze_naive(frequency: str = "h",ax:Axes = None)->Axes:
    FILE_DIR = OUTPUTS_DIR / "naive.parquet"
    df = pd.read_parquet(FILE_DIR)
    df = df.resample(frequency).mean().dropna()

    ax = df.plot(y=["actual_price","predicted_price"],kind="line",ax=ax)

    return ax