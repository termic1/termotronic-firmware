# ============================================================
# Termotronic Programmer — Unified Config
# ============================================================
# This file defines ONLY stable hardware constants.
# All dynamic behavior (flash params, profiles, rules) lives in JSON.
# ============================================================


# ------------------------------------------------------------
# LED GPIO Pins (Orange Pi / WiringOP numbering)
# ------------------------------------------------------------
LED_RED = 2
LED_GREEN = 3
LED_BLUE = 4


# ------------------------------------------------------------
# Optional GPIO for future expansion
# ------------------------------------------------------------
RESET_PIN = 6
BOOT_PIN = 7
POWER_ENABLE_PIN = 8


# ------------------------------------------------------------
# Web server configuration
# ------------------------------------------------------------
WEB_PORT = 8080


# ------------------------------------------------------------
# mDNS service name
# ------------------------------------------------------------
MDNS_NAME = "termotronic.local"
MDNS_SERVICE = "Termotronic Programmer"


# ------------------------------------------------------------
# Storage files (inside repo root)
# ------------------------------------------------------------
CONF_FILE = "conf.json"
COUNTER_FILE = "counter.json"
