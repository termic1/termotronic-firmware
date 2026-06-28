import json
import os
from datetime import date

from config import CONF_FILE, COUNTER_FILE


# ============================================================
# JSON Helpers
# ============================================================

def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


# ============================================================
# Load State (conf.json + counter.json)
# ============================================================

def load_state():
    """
    Loads programmer state (conf.json) and monthly counters (counter.json).
    Ensures unified repo structure and per-version stats exist.
    """

    # Default conf.json structure
    default_conf = {
        "PWD": "v5307110",
        "VER": "100",

        "CURRENT_YEAR": str(date.today().year),
        "CURRENT_MONTH": date.today().strftime("%b").lower(),

        "CURRENT_MONTH_PO": "0",
        "CURRENT_MONTH_NE": "0",

        "CURRENT_FIRMWARE": "v1.0",

        # Per-version statistics
        "versions": {}
    }

    datos = load_json(CONF_FILE, default_conf)
    cuenta = load_json(COUNTER_FILE, {})

    # Ensure CURRENT_FIRMWARE exists
    if "CURRENT_FIRMWARE" not in datos:
        datos["CURRENT_FIRMWARE"] = "v1.0"

    # Ensure per-version stats dict exists
    if "versions" not in datos:
        datos["versions"] = {}

    return datos, cuenta


# ============================================================
# Save State
# ============================================================

def save_state(datos, cuenta):
    save_json(CONF_FILE, datos)
    save_json(COUNTER_FILE, cuenta)


# ============================================================
# Month Rotation
# ============================================================

def rotate_month(datos, cuenta):
    """
    Moves CURRENT_MONTH_PO and CURRENT_MONTH_NE into counter.json
    under the correct year/month, then resets monthly counters.
    """

    today = date.today()

    old_year = datos["CURRENT_YEAR"]
    old_month = datos["CURRENT_MONTH"]

    # Ensure year exists in counter.json
    if old_year not in cuenta:
        cuenta[old_year] = [{}, {}]  # PO dict, NE dict

    # Store monthly stats
    cuenta[old_year][0][old_month] = datos["CURRENT_MONTH_PO"]
    cuenta[old_year][1][old_month] = datos["CURRENT_MONTH_NE"]

    # Reset for new month
    datos["CURRENT_YEAR"] = str(today.year)
    datos["CURRENT_MONTH"] = today.strftime("%b").lower()
    datos["CURRENT_MONTH_PO"] = "0"
    datos["CURRENT_MONTH_NE"] = "0"

    save_state(datos, cuenta)
