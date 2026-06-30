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
    print("\n=== THERMOHEAT UNIVERSAL FLASHER ===\n")

    if len(sys.argv) < 3:
        print("Usage:")
        print("  flasher.py <programmer_settings.json> <firmware_folder>")
        sys.exit(1)

    programmer_settings_path = sys.argv[1]
    firmware_folder = sys.argv[2]

    # Load programmer settings (chip-specific)
    settings = load_json(programmer_settings_path)

    # Turn off all LEDs before starting
    leds_all_off()

    chip = settings["chip"]
    print(f"[INFO] Target chip: {chip}")

    # ---------------------------------------------------------
    # ERASE FLASH
    # ---------------------------------------------------------
    if settings["erase"]["enabled"]:
        print("[INFO] Erasing flash...")
        try:
            led_on(LED_GREEN)  # green = working
            erase_cmd = build_erase_cmd(settings)
            run_esptool(erase_cmd)
        except Exception:
            led_off(LED_GREEN)
            led_on(LED_RED)  # red = error
            sys.exit(1)

    # ---------------------------------------------------------
    # WRITE FLASH
    # ---------------------------------------------------------
    print("[INFO] Writing flash...")
    try:
        write_cmd = build_write_cmd(settings, firmware_folder)
        run_esptool(write_cmd)
    except Exception:
        led_off(LED_GREEN)
        led_on(LED_RED)  # red = error
        sys.exit(1)

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------
    led_off(LED_GREEN)
    led_on(LED_BLUE)  # blue = success

    print("\n=== FLASHING COMPLETE ===")
    print("[SUCCESS] Device flashed successfully!")


if __name__ == "__main__":
    main()
