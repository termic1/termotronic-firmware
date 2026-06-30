import os
import time
import threading
import json
import socket
from datetime import date

from flask import Flask, jsonify, render_template, Response
from zeroconf import ServiceInfo, Zeroconf

from flasher import flash_device, all_off
from storage import load_state, save_state, rotate_month
from config import LED_RED, LED_GREEN, LED_BLUE


# ============================================================
# PATHS — Unified Repo Structure
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = BASE_DIR

MANIFEST = os.path.join(REPO_ROOT, "manifest.json")
FIRMWARE_DIR = os.path.join(REPO_ROOT, "firmware")
COMMON_DIR = os.path.join(REPO_ROOT, "common")
PROGRAMMER_DIR = os.path.join(REPO_ROOT, "programmer")
WEB_DIR = os.path.join(REPO_ROOT, "web")


# ============================================================
# Helpers
# ============================================================

def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)

live_log = []

def add_log(msg):
    print(msg)
    live_log.append(msg)
    
def all_off():
    leds_all_off()


# ============================================================
# Flask Web Server
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(WEB_DIR, "templates"),
    static_folder=os.path.join(WEB_DIR, "static")
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logs")
def logs():
    datos, cuenta = load_state()
    return jsonify({"current": datos, "history": cuenta})

@app.route("/live")
def live():
    return jsonify(live_log[-50:])

@app.route("/stream")
def stream():
    def event_stream():
        last = 0
        while True:
            if len(live_log) > last:
                for line in live_log[last:]:
                    yield f"data: {line}\n\n"
                last = len(live_log)
            time.sleep(0.5)
    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/firmware_list")
def firmware_list():
    manifest = load_manifest()
    return jsonify(list(manifest["versions"].keys()))

@app.route("/active_firmware")
def active_firmware():
    datos, _ = load_state()
    return jsonify({"active": datos["CURRENT_FIRMWARE"]})

@app.route("/stats")
def stats():
    datos, cuenta = load_state()
    return jsonify({
        "current_month": {
            "month": datos["CURRENT_MONTH"],
            "po": datos["CURRENT_MONTH_PO"],
            "ne": datos["CURRENT_MONTH_NE"]
        },
        "versions": datos.get("versions", {}),
        "history": cuenta
    })

@app.route("/set_firmware/<version>")
def set_firmware(version):
    datos, cuenta = load_state()
    manifest = load_manifest()

    if version not in manifest["versions"]:
        return jsonify({"error": "Version not found"}), 404

    datos["CURRENT_FIRMWARE"] = version
    save_state(datos, cuenta)
    add_log(f"Firmware version set to {version}")

    return jsonify({"status": "ok", "version": version})

@app.route("/sync_repo")
def sync_repo():
    os.system(f"cd {REPO_ROOT} && git pull")
    add_log("Repository synced from GitHub")
    return "OK"


# ============================================================
# mDNS
# ============================================================

def start_mdns():
    hostname = "termotronic.local."
    ip = socket.gethostbyname(socket.gethostname())

    info = ServiceInfo(
        "_http._tcp.local.",
        "Termotronic Programmer._http._tcp.local.",
        addresses=[socket.inet_aton(ip)],
        port=8080,
        properties={},
        server=hostname,
    )

    zeroconf = Zeroconf()
    zeroconf.register_service(info)
    add_log("mDNS active: http://termotronic.local")


# ============================================================
# USB Monitor
# ============================================================

def get_usb():
    return os.popen("lsusb").read().strip().split("\n")

def get_dev():
    return os.listdir("/dev")

def diff(old, new):
    return [x for x in new if x not in old], [x for x in old if x not in new]


def monitor_loop():
    old_usb = get_usb()
    old_dev = get_dev()

    while True:
        time.sleep(1)

        # Reload state every loop so UI changes take effect
        datos, cuenta = load_state()

        # Month rotation
        current_month = date.today().strftime("%b").lower()
        if current_month != datos["CURRENT_MONTH"]:
            rotate_month(datos, cuenta)

        usb_now = get_usb()
        dev_now = get_dev()

        usb_added, usb_removed = diff(old_usb, usb_now)
        dev_added, dev_removed = diff(old_dev, dev_now)

        # Device added
        for dev in dev_added:
            if dev.startswith("ttyACM"):
                add_log(f"Detected device: {dev}")

                manifest = load_manifest()
                fw = datos["CURRENT_FIRMWARE"]

                if fw not in manifest["versions"]:
                    add_log(f"Firmware {fw} not found in manifest")
                    continue

                # Load version-specific files
                files = manifest["versions"][fw]["files"]
                bootloader = os.path.join(REPO_ROOT, files["bootloader"])
                partitions = os.path.join(REPO_ROOT, files["partitions"])
                firmware = os.path.join(REPO_ROOT, files["firmware"])

                # Load common boot_app0
                boot_app0 = os.path.join(REPO_ROOT, manifest["common"]["boot_app0"])

                # Load version-specific config.json
                config_path = os.path.join(REPO_ROOT, manifest["versions"][fw]["config"])
                fw_config = json.load(open(config_path))

                # Load programmer profiles
                prog_settings_path = os.path.join(REPO_ROOT, fw_config["programmer_profiles"]["settings"])
                prog_rules_path = os.path.join(REPO_ROOT, fw_config["programmer_profiles"]["rules"])

                prog_settings = json.load(open(prog_settings_path))
                prog_rules = json.load(open(prog_rules_path))

                ok = flash_device(
                    bootloader,
                    partitions,
                    boot_app0,
                    firmware,
                    fw_config,
                    prog_settings,
                    prog_rules,
                    dev,
                    add_log
                )

                if ok:
                    datos["CURRENT_MONTH_PO"] = str(int(datos["CURRENT_MONTH_PO"]) + 1)
                    add_log("Flash SUCCESS")
                else:
                    datos["CURRENT_MONTH_NE"] = str(int(datos["CURRENT_MONTH_NE"]) + 1)
                    add_log("Flash FAILED")

                save_state(datos, cuenta)

        # Device removed
        for dev in dev_removed:
            if dev.startswith("ttyACM"):
                all_off()
                add_log(f"Device removed: {dev}")

        old_usb = usb_now
        old_dev = dev_now


# ============================================================
# Start System
# ============================================================

if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()
    threading.Thread(target=start_mdns, daemon=True).start()

    add_log("Termotronic Programmer Started")
    app.run(host="0.0.0.0", port=8080)
