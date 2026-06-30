#!/usr/bin/env python3
import os
import sys
import json
import traceback
import esptool


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


def print_header(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def run_esptool(cmd):
    print(f"[CMD] esptool.py {' '.join(cmd)}")
    try:
        esptool.main(cmd)
    except SystemExit:
        # esptool uses SystemExit internally; ignore normal exit
        pass
    except Exception as e:
        print("[ERROR] esptool failed:")
        print(e)
        traceback.print_exc()
        sys.exit(1)


def validate_settings(settings):
    required = ["chip", "erase", "flash", "memory", "write_layout", "reset"]
    for key in required:
        if key not in settings:
            print(f"[ERROR] Missing required key in programmer settings: {key}")
            sys.exit(1)

    if "enabled" not in settings["erase"]:
        print("[ERROR] erase.enabled missing")
        sys.exit(1)

    flash_keys = ["baud", "mode", "freq", "size"]
    for fk in flash_keys:
        if fk not in settings["flash"]:
            print(f"[ERROR] flash.{fk} missing")
            sys.exit(1)

    if not isinstance(settings["write_layout"], list):
        print("[ERROR] write_layout must be a list")
        sys.exit(1)


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


def main():
    print_header("THERMOHEAT UNIVERSAL ESP FLASHER")

    if len(sys.argv) < 3:
        print("Usage:")
        print("  flasher.py <programmer_settings.json> <firmware_folder>")
        sys.exit(1)

    programmer_settings_path = sys.argv[1]
    firmware_folder = sys.argv[2]

    print(f"[INFO] Loading programmer settings: {programmer_settings_path}")
    settings = load_json(programmer_settings_path)
    validate_settings(settings)

    chip = settings["chip"]
    print(f"[INFO] Target chip: {chip}")

    # PSRAM info
    psram = settings["memory"]["psram"]
    if psram["supported"]:
        print(f"[INFO] PSRAM: {psram['type']} @ {psram.get('speed', 'N/A')}")
    else:
        print("[INFO] PSRAM: Not supported")

    # ERASE FLASH
    if settings["erase"]["enabled"]:
        print_header("ERASE FLASH")
        erase_cmd = build_erase_cmd(settings)
        run_esptool(erase_cmd)
    else:
        print("[INFO] Erase disabled in settings")

    # WRITE FLASH
    print_header("WRITE FLASH")
    write_cmd = build_write_cmd(settings, firmware_folder)
    run_esptool(write_cmd)

    print_header("FLASHING COMPLETE")
    print("[SUCCESS] Device flashed successfully!")


if __name__ == "__main__":
    main()
