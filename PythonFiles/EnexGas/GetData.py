import requests as r
from bs4 import BeautifulSoup 
from PythonFiles.Tools.Dates import get_dates
from PythonFiles.Tools.files import get_data_path
from datetime import datetime
import zipfile
import io
from pathlib import Path
import pandas as pd 
import time
import random
import sys

PATH = Path(__file__).parent / "Resources"

HENEX = "https://www.enexgroup.gr/"
GAS_LIST = "el/web/guest/gas-official-list?"
DOCUMENTS =  "documents/20126/997118/"
arg = "p_p_id_com_liferay_asset_publisher_web_portlet_AssetPublisherPortlet_INSTANCE_v2cho0fcNMrv_"

def get_data():
    starts_at, ends_at = get_dates()

    starts_at = starts_at - pd.Timedelta(days=1) #we only really care for day ahead since activity on the others is minimal
    ends_at = ends_at - pd.Timedelta(days=1)
    now = datetime.now()
    cur_year = now.year
    uuids = dict()
    seen = set()
    prev_years = []

    if(cur_year > starts_at.year):
        for year in range(starts_at.year,cur_year):
            if(year > ends_at.year): break
            prev_years.append(year)
        original_start = starts_at
        starts_at = pd.Timestamp(year=cur_year,month=1,day=1, tz="UTC")

    print(prev_years)

    if(len(prev_years) > 0):
        index = 1
        run = True
        while(run): 
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
                    uuids[year] = href.get("href")
            index+=1
            time.sleep(random.uniform(5.0,3.0))
    #now we have all uuids for previous years

    for year in prev_years:
        uuid = uuids[year]
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

    if(len(prev_years) > 0):
        SAVE_DIR = PATH / (str(original_start.year) + "_NGAS_DOL")
        files = SAVE_DIR.iterdir()
        for f in files:
            file_date = pd.to_datetime(f.name.split("_")[0],format="%Y%m%d").date()
            if(original_start.date() > file_date or ends_at.date() < file_date):
                f.unlink(missing_ok=True)


    SAVE_DIR =PATH / (str(cur_year) + "_NGAS_DOL")
    for d in pd.date_range(starts_at.date(), ends_at.date(), freq="D"):
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