# main.py — Pi Switch controller using JSON pin mapping
# Files on CIRCUITPY:
#   - pins.json      (required)
#   - config.json    (optional: invert/deadzone/trigger min/max)
#
# boot.py (HID descriptor) remains the same as before.

import time, json, csv, board, digitalio, analogio, usb_hid

PINS_FILE = "button-pinout.json"
CONFIG_FILE = "config.json"  # optional

def _resolve_pin(label: str):
    label = (label or "").strip()
    # Normalize "MOSI (D4)" -> "D4"
    if "(" in label and ")" in label:
        inner = label[label.find("(")+1:label.find(")")]
        if inner in dir(board):
            return getattr(board, inner)
    if label in dir(board):
        return getattr(board, label)
    raise ValueError("Unknown pin label: " + label)

def _load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

# ---- Load mapping + optional config ----
mapping = _load_json(PINS_FILE, default=None)
assert mapping is not None, "pins.json not found or invalid"

BUTTONS = mapping.get("buttons", {})
DPAD    = mapping.get("dpad",    {})
AXES    = mapping.get("axes",    {})

CONFIG  = _load_json(CONFIG_FILE, default={})
INV     = CONFIG.get("invert", {})            # e.g. {"LY": true, "RY": true}
DZ      = CONFIG.get("deadzone", {})          # e.g. {"LX": 12, "LY": 12}
TCFG    = CONFIG.get("triggers", {})          # e.g. {"LT_min": 20, "LT_max": 240, "RT_min": 15, "RT_max": 250}

# ---- Init GPIO ----
btn_ios = []
for name, pin_label in BUTTONS.items():
    p = digitalio.DigitalInOut(_resolve_pin(pin_label))
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP  # active-low to GND
    btn_ios.append((name, p))

dpad_ios = {}
for k in ("Up","Down","Left","Right"):
    pin_label = DPAD.get(k)
    if pin_label:
        io = digitalio.DigitalInOut(_resolve_pin(pin_label))
        io.direction = digitalio.Direction.INPUT
        io.pull = digitalio.Pull.UP
        dpad_ios[k] = io

def _ain(label):
    return analogio.AnalogIn(_resolve_pin(label)) if label else None

ain = {}
for key in ("LX","LY","RX","RY","LT","RT"):
    pin = AXES.get(key)
    if pin:
        ain[key] = _ain(pin)

# ---- HID device (from your existing boot.py descriptor) ----
gp = None
for dev in usb_hid.devices:
    if dev.usage_page == 0x01 and dev.usage == 0x05:
        gp = dev
        break
assert gp is not None, "Gamepad HID device not found (check boot.py)"

# ---- Helpers ----
def _hat(u, d, l, r):
    # 0=N,1=NE,2=E,3=SE,4=S,5=SW,6=W,7=NW,8=neutral
    if u and not d and not l and not r: return 0
    if u and r: return 1
    if r and not u and not d: return 2
    if d and r: return 3
    if d and not r and not l: return 4
    if d and l: return 5
    if l and not d and not u: return 6
    if u and l: return 7
    return 8

def _btn(io):  # active-low
    return 0 if io.value else 1

def _axis(a, name=None):
    if not a: return 128
    val = a.value >> 8  # 0..255
    # invert
    if name and INV.get(name, False):
        val = 255 - val
    # deadzone (sticks)
    if name in DZ:
        dz = int(DZ[name])
        if abs(val - 128) < dz:
            val = 128
    # trigger calibration
    if name in ("LT","RT"):
        lo = int(TCFG.get(name + "_min", 0))
        hi = int(TCFG.get(name + "_max", 255))
        if hi > lo:
            val = max(0, min(255, int((val - lo) * 255 / (hi - lo))))
    return val

# Deterministic button ordering: alphabetical by name
button_order = sorted([nm for nm,_ in btn_ios])

# ---- Main loop ----
while True:
    bits = 0
    for i, name in enumerate(button_order):
        for nm, io in btn_ios:
            if nm == name and _btn(io):
                bits |= (1 << i)
                break

    u = _btn(dpad_ios.get("Up"))    if dpad_ios.get("Up")    else 0
    d = _btn(dpad_ios.get("Down"))  if dpad_ios.get("Down")  else 0
    l = _btn(dpad_ios.get("Left"))  if dpad_ios.get("Left")  else 0
    r = _btn(dpad_ios.get("Right")) if dpad_ios.get("Right") else 0
    hat = _hat(u, d, l, r)

    lx = _axis(ain.get("LX"), "LX")
    ly = _axis(ain.get("LY"), "LY")
    rx = _axis(ain.get("RX"), "RX")
    ry = _axis(ain.get("RY"), "RY")
    lt = _axis(ain.get("LT"), "LT")
    rt = _axis(ain.get("RT"), "RT")

    report = bytes([bits & 0xFF, (bits >> 8) & 0xFF, hat, lx, ly, rx, ry, lt, rt])
    gp.send_report(report)
    time.sleep(0.01)  # ~100 Hz