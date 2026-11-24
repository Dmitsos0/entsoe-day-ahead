import requests as r
from bs4 import BeautifulSoup 
from PythonFiles.Tools.Dates import get_dates,get_missing,get_missing_years
from PythonFiles.Tools.files import get_data_path
from datetime import datetime
import zipfile
import io
from pathlib import Path
import pandas as pd 
import time
import random
import sys
import json
PATH = Path(__file__).parent / "Resources"
UUIDS_DIR = Path(__file__).parent 
UUIDS_PATH = UUIDS_DIR / "uuids.json"
HENEX = "https://www.enexgroup.gr/"
GAS_LIST = "el/web/guest/gas-official-list?"
DOCUMENTS =  "documents/20126/997118/"
arg = "p_p_id_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_v2cho0fcNMrv_"

def get_data():
    print("getting gas prices...")
    starts_at, ends_at = get_dates()

    starts_at = starts_at - pd.Timedelta(days=1) #we only really care for day ahead since activity on the others is minimal
    ends_at = ends_at - pd.Timedelta(days=1)
    missing_timestamps = get_missing(PATH,starts_at,ends_at,column="Trading Date")
    now = datetime.now()
    cur_year = now.year
    seen = set()

    missing_years: set[pd.Timestamp] = set()
    if(cur_year > starts_at.year):
        missing_years = get_missing_years(missing_timestamps)

    if(cur_year in missing_years): missing_years.remove(cur_year)
    missing_uuids= dict()
    if(UUIDS_PATH.exists()):
        with UUIDS_PATH.open(mode="r") as f:
            missing_uuids = json.load(f)
    missing = False

    for year in missing_years:
        if(str(year) not in missing_uuids.keys()):
            print(str(year), f" missing_uuids keys: {missing_uuids.keys()}")
            missing = True
            break
    
    if(missing):
        index = 1
        run = True
        while(run): 
            print(index)
            url = HENEX + GAS_LIST + f"p_p_id=com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_v2cho0fcNMrv&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_v2cho0fcNMrv_redirect=%2Fel%2Fgas-official-list&_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_v2cho0fcNMrv_delta=10&p_r_p_resetCur=false&_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_v2cho0fcNMrv_cur={index}"
            response = r.get(url,timeout=30)
            if response.status_code != 200:
                print(f"bad connection with status code: {response.status_code}, potentially a url change or rate limit triggered please report this to me")
                sys.exit()    
            soup = BeautifulSoup(response.text, "html.parser")

            result = soup.find("div", id=arg)
            if result is None:
                break
            items = result.find_all("div", class_="asset-abstract")
            if not items:          
                break

            for div in items:
                href = div.find("a")
                if href is None:   
                    continue
                text = href.text.strip()
                if text in seen:
                    run = False
                    break
                seen.add(text)
                arg1 = text.split("_")[0]
                year = int(arg1[:4])
                if(year < cur_year): 
                    missing_uuids[year] = href.get("href")
                    
            index+=1
            time.sleep(random.uniform(5.0,3.0))
    #now we have all uuids for previous years
    UUIDS_DIR.mkdir(parents=True,exist_ok=True)
    with UUIDS_PATH.open(mode="w") as f:
        json.dump(missing_uuids,f)

    for year in missing_years:
        print(year)
        uuid = missing_uuids[str(year)]
        url = HENEX + uuid
        response = r.get(url,timeout=30)
        if response.status_code != 200:
            print(f"bad connection with status code: {response.status_code}, potentially a url change or rate limit triggered please report this to me")
            sys.exit()
        target = PATH / f"{year}_NGAS_DOL"
        target.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            for member in z.infolist():
                if member.is_dir():
                    continue
                filename = Path(member.filename).name  
                if filename:
                    (target / filename).write_bytes(z.read(member))


    SAVE_DIR =PATH / (str(cur_year) + "_NGAS_DOL")
    for tup in missing_timestamps:
        if(tup[0] != cur_year): continue 
        for d in pd.date_range(tup[0].date(), tup[1].date(), freq="D"):
            name = f"{d:%Y%m%d}"
            url = f"{HENEX}{DOCUMENTS}{name}_NGAS_DOL_EN_v01.xlsx"
            response = r.get(url, timeout=30)
            if response.status_code == 404:
                continue
            elif response.status_code != 200:
                print(f"bad connection with status code: {response.status_code}, potentially a url change or rate limit triggered please report this to me")
                sys.exit()
            SAVE_DIR.mkdir(parents=True, exist_ok=True)
            (SAVE_DIR / f"{name}_NGAS_DOL_EN_v01.xlsx").write_bytes(response.content)
            time.sleep(random.uniform(1.0, 2.0))
        




def analyze_data():
    frames = []
    for folder in PATH.iterdir():
        if folder.is_dir():
            for file in folder.iterdir():
                if file.suffix != ".xlsx":
                    continue
                timestamp = pd.to_datetime(file.name.split("_")[0]).tz_localize("UTC")
                timestamp = timestamp + pd.Timedelta(days=1) #+1 so the day ahead prices paid are matched with the day they actually impact
                temp = pd.read_excel(file)
                temp = temp.drop(columns=["HGMSI","HGMBI","HGSIDA","HGSIWD","VWAP MWh Pre Agreed",
                                   "Traded Volume Pre Agreed (MWh)","Traded Quanity (No of Contracts)",
                                   "Previous Closing Price","Traded Volume (MWh)","Trading Date","Closing Price","Number of Trades","Start Price","Min Price","Last Price", "Max Price","Number of Orders","Trading Series\n",
                                   ],axis="columns")
                temp["timestamp"] = timestamp
                temp = temp[~temp["Contract"].isin(["WD","D+2","D+3","WE"])]
                frames.append(temp)
    df = pd.concat(frames,ignore_index=True) 
    df = df.sort_values("timestamp").reset_index(drop=True)
    DATA_PATH = get_data_path()
    SAVE_DIR = DATA_PATH / "gas"
    SAVE_DIR.mkdir(parents=True,exist_ok=True)
    path = SAVE_DIR / "gas.parquet"
    df = df.fillna(0)
    df.to_parquet(path,index=False)

    
def get_all_enex_gas():
    get_data()
    time.sleep(3) #make sure the files are all ok before trying to load them
    analyze_data()

if __name__ == "__main__": # for testing purposes 
    get_data()