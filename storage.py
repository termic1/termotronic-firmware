import json, os
from datetime import date
from config import ROOT

CONF_FILE = ROOT + "conf.json"
COUNT_FILE = ROOT + "counter.json"

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load_state():
    datos = load_json(CONF_FILE, {
        "PWD": "v5307110",
        "VER": "100",
        "CURRENT_YEAR": "2023",
        "CURRENT_MONTH": "jan",
        "CURRENT_MONTH_PO": "0",
        "CURRENT_MONTH_NE": "0",
        "CURRENT_FIRMWARE": "v1.0",
        "versions": {}              # ⭐ NEW: per-version stats
    })

    cuenta = load_json(COUNT_FILE, {})
    return datos, cuenta

def save_state(datos, cuenta):
    save_json(CONF_FILE, datos)
    save_json(COUNT_FILE, cuenta)

def rotate_month(datos, cuenta):
    today = date.today()
    old_year = datos["CURRENT_YEAR"]
    old_month = datos["CURRENT_MONTH"]

    if old_year not in cuenta:
        cuenta[old_year] = [{}, {}]

    cuenta[old_year][0][old_month] = datos["CURRENT_MONTH_PO"]
    cuenta[old_year][1][old_month] = datos["CURRENT_MONTH_NE"]

    datos["CURRENT_YEAR"] = str(today.year)
    datos["CURRENT_MONTH"] = today.strftime("%b").lower()
    datos["CURRENT_MONTH_PO"] = "0"
    datos["CURRENT_MONTH_NE"] = "0"

    save_state(datos, cuenta)
