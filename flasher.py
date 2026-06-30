#!/usr/bin/env python3
import os
import sys
import json
import traceback
import esptool
import subprocess

# ---------------------------------------------------------
# IMPORT LED PINS FROM config.py (single source of truth)
# ---------------------------------------------------------
try:
    from config import LED_RED, LED_GREEN, LED_BLUE
except Exception as e:
    print("[ERROR] Cannot import LED pins from config.py")
    print(e)
    sys.exit(1)


# ---------------------------------------------------------
# GPIO Helpers
# ---------------------------------------------------------
def gpio_write(pin, value):
    subprocess.call(f"gpio write {pin} {value}", shell=True)

def led_on(pin):
    gpio_write(pin, 1)

def led_off(pin):
    gpio_write(pin, 0)

def leds_all_off():
    led_off(LED_RED)
    led_off(LED_GREEN)
    led_off(LED_BLUE)


# ---------------------------------------------------------
# JSON Loader
# ---------------------------------------------------------
def load_json(path):
    if not os.path.exists(path):
        print(f"[ERROR] JSON file not found: {path}")
        sys.exit(1)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {path}")
        print(e)
        sys.exit(1)


# ---------------------------------------------------------
# ESPLTOOL Runner
# ---------------------------------------------------------
def run_esptool(cmd):
    print(f"[CMD] esptool.py {' '.join(cmd)}")
    try:
        esptool.main(cmd)
    except SystemExit:
        pass
    except Exception as e:
        print("[ERROR] esptool failed:")
        print(e)
        traceback.print_exc()
        raise


# ---------------------------------------------------------
# Command Builders
# ---------------------------------------------------------
def build_erase_cmd(settings):
    return [
        "--chip", settings["chip"],
        "erase_flash"
    ]

def build_write_cmd(settings, firmware_folder):
    flash = settings["flash"]

    cmd = [
        "--chip", settings["chip"],
        "--baud", str(flash["baud"]),
        "--flash_mode", flash["mode"],
        "--flash_freq", flash["freq"],
        "--flash_size", flash["size"],
        "write_flash",
        "-z"
    ]

    for entry in settings["write_layout"]:
        address = entry["address"]
        file_path = os.path.join(firmware_folder, entry["file"])

        if not os.path.exists(file_path):
            print(f"[ERROR] Firmware file missing: {file_path}")
            sys.exit(1)

        cmd.append(address)
        cmd.append(file_path)

    return cmd


# ---------------------------------------------------------
# MAIN FLASHER
# ---------------------------------------------------------
def main():
    print("\
