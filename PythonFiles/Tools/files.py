from dotenv import load_dotenv
import sys
from pathlib import Path
from pandas import Timestamp
from os import getenv

def load_env(): # this function is made to only load the default environment 
    if(not load_dotenv()):
        print("you have not made a .env file check the README file for further instructions")
        sys.exit()

def get_data_path()-> Path :
    TOOLS_DIR = Path(__file__).resolve().parent
    PYTHONFILES_DIR = TOOLS_DIR.parent
    PROJECT_DIR = PYTHONFILES_DIR.parent
    DATA_DIR = PROJECT_DIR / "Data"
    return DATA_DIR

def get_tools_path() -> Path:
    TOOLS_DIR = Path(__file__).resolve().parent
    return TOOLS_DIR

def get_pythonfiles_path() -> Path:
    TOOLS_DIR = Path(__file__).resolve().parent
    PYTHONFILES_DIR = TOOLS_DIR.parent
    return PYTHONFILES_DIR

def get_project_dir()-> Path:
    TOOLS_DIR = Path(__file__).resolve().parent
    PYTHONFILES_DIR = TOOLS_DIR.parent
    PROJECT_DIR = PYTHONFILES_DIR.parent
    return PROJECT_DIR



