import os
import esptool
import subprocess
import json

from config import LED_RED, LED_GREEN, LED_BLUE


# ============================================================
# GPIO / LED Helpers
# ============================================================

def gpio_write(pin, value):
    subprocess.call(f"gpio write {pin} {value}", shell=True)


def gpio_on(pin):
    gpio_write(pin, 1)


def gpio_off(pin):
    gpio_write(pin, 0)


def all_off():
    gpio_off(LED_RED)
    gpio_off(LED_GREEN)
    gpio_off(LED_BLUE)


def apply_led_behavior(settings, state):
    """
    state: "flashing", "success", "failure"
    settings['behavior'] defines which LED to use for each state.
    """
    behavior = settings.get("behavior", {})
    led_map = {
        "success": behavior.get("led_success", "blue"),
        "failure": behavior.get("led_failure", "red"),
        "flashing": behavior.get("led_flashing", "green"),
    }

    # Turn all off first
    all_off()

    led = led_map.get(state)
    if led == "red":
        gpio_on(LED_RED)
    elif led == "green":
        gpio_on(LED_GREEN)
    elif led == "blue":
        gpio_on(LED_BLUE)


# ============================================================
# Pre‑Flash Checks (Rules)
# ============================================================

def prechecks_ok(rules, log):
    env = rules.get("environment", {})
    safety = rules.get("safety", {})
    logging_cfg = rules.get("logging", {})

    if logging_cfg.get("log_prechecks", True):
        log("Running pre-flash checks (environment, jig, usb)...")

    # TODO: replace these placeholders with real sensor readings
    voltage_ok = True
    temp_ok = True
    jig_ok = True
    usb_ok = True

    if safety.get("block_if_voltage_low", True) and not voltage_ok:
        log("Blocked: voltage too low")
        return False

    if safety.get("block_if_temperature_high", True) and not temp_ok:
        log("Blocked: temperature too high")
        return False

    if safety.get("block_if_jig_missing", True) and not jig_ok:
        log("Blocked: jig missing")
        return False

    if safety.get("block_if_usb_unstable", True) and not usb_ok:
        log("Blocked: USB unstable")
        return False

    return True


# ============================================================
# Esptool Command Builder
# ============================================================

def build_esptool_cmd(bootloader, partitions, boot_app0, firmware, fw_config, devPORT):
    flash = fw_config.get("flash", {})

    baud = str(flash.get("baud", 460800))
    erase = flash.get("erase", "yes")
    offset = flash.get("offset", "0x10000")
    flash_mode = flash.get("flash_mode", "dio")
    flash_freq = flash.get("flash_freq", "80m")
    flash_size = flash.get("flash_size", "4MB")

    cmd = [
        "--chip", "esp32c3",
        "--port", devPORT,
        "--baud", baud,
        "--before", "default_reset",
        "--after", "hard_reset",
    ]

    if erase == "yes":
        cmd += ["erase_flash"]

    cmd += [
        "write_flash", "-z",
        "0x0", bootloader,
        "0x8000", partitions,
        "0xe000", boot_app0,
        offset, firmware,
        "--flash_mode", flash_mode,
        "--flash_freq", flash_freq,
        "--flash_size", flash_size,
    ]

    return cmd


# ============================================================
# Main Flash Function
# ============================================================

def flash_device(
    bootloader,
    partitions,
    boot_app0,
    firmware,
    fw_config,
    prog_settings,
    prog_rules,
    devPORT,
    log,
):
    """
    bootloader, partitions, boot_app0, firmware:
        Full paths to binary files.

    fw_config:
        Dict from firmware/vX.Y/config.json

    prog_settings:
        Dict from programmer/settings_*.json

    prog_rules:
        Dict from programmer/rules_*.json

    devPORT:
        e.g. "ttyACM0" (without /dev/)

    log:
        Function(msg) -> None
    """

    devPORT = "/dev/" + devPORT

    # LED: flashing state
    apply_led_behavior(prog_settings, "flashing")
    log(f"Starting flash on {devPORT}")
    log(f"Bootloader: {bootloader}")
    log(f"Partitions: {partitions}")
    log(f"Boot_app0: {boot_app0}")
    log(f"Firmware: {firmware}")

    # Prechecks based on programmer rules
    if not prechecks_ok(prog_rules, log):
        apply_led_behavior(prog_settings, "failure")
        return False

    # Build esptool command
    cmd = build_esptool_cmd(bootloader, partitions, boot_app0, firmware, fw_config, devPORT)
    log(f"Esptool command: {cmd}")

    try:
        esptool.main(cmd)
        apply_led_behavior(prog_settings, "success")
        log("Flash SUCCESS")
        return True

    except Exception as e:
        apply_led_behavior(prog_settings, "failure")
        log(f"Flash FAILED: {e}")
        return False
