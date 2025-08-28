# main.py — Custom HID gamepad (ItsyBitsy M0 Express)
# Requires:
#   - boot.py              (defines 9-byte HID: 16 buttons, hat, 6 axes)
#   - button-pinout.json   (pin mapping)
#   - config.json          (invert, deadzone, smoothing, trigger calibration)
#
# Design:
#   - Buttons & D-pad: event-driven via keypad.Keys (less USB chatter, built-in debounce)
#   - Sticks + triggers: polled analog (continuous), then tuned by config and packed into HID
#   - Axes are sent as 8-bit (0..255) values to match the 1-byte-per-axis HID descriptor

import time, json, board, analogio, usb_hid, keypad

PINS_FILE   = "button-pinout.json"
CONFIG_FILE = "config.json"

# ---------- JSON loader (supports // comments) ----------
def load_json(path, default=None):
    try:
        with open(path, "r") as f:
            lines = []
            for line in f:
                if line.lstrip().startswith("//"):
                    continue
                lines.append(line)
            return json.loads("".join(lines))
    except Exception:
        return default

# ---------- Pin resolver ("MOSI (D4)" -> D4, etc.) ----------
def resolve_pin(label: str):
    label = (label or "").strip()
    # Allow forms like "MOSI (D4)" -> prefer inner D4 if present
    if "(" in label and ")" in label:
        inner = label[label.find("(")+1:label.find(")")]
        if inner in dir(board):
            return getattr(board, inner)
    # Direct names like "D9", "A0"
    if label in dir(board):
        return getattr(board, label)
    raise ValueError("Unknown pin label: " + label)

# ---------- Load mapping & config ----------
mapping = load_json(PINS_FILE)
assert mapping is not None, f"{PINS_FILE} not found or invalid"

config   = load_json(CONFIG_FILE, default={})
INVERT   = config.get("invert",   {})   # e.g. {"LY": true, "RY": true}
DEADZONE = config.get("deadzone", {})   # raw 0..255 delta around 128
SMOOTH   = config.get("smoothing", {})  # 0.0..1.0 per axis
TRIG     = config.get("triggers", {})   # {LT_min, LT_max, RT_min, RT_max}

# Deterministic host button order (typical Xbox-like expectation)
BUTTON_ORDER = ["A","B","X","Y","LB","RB","Start","Select","L3","R3"]
button_names = [nm for nm in BUTTON_ORDER if nm in mapping["buttons"]]
button_pins  = [resolve_pin(mapping["buttons"][nm]) for nm in button_names]

# D-pad (Up, Down, Left, Right) — each is its own input, mapped to an 8-way hat
dpad_pins = [
    resolve_pin(mapping["dpad"]["Up"]),
    resolve_pin(mapping["dpad"]["Down"]),
    resolve_pin(mapping["dpad"]["Left"]),
    resolve_pin(mapping["dpad"]["Right"]),
]

# ---------- Hardware setup ----------
buttons = keypad.Keys(button_pins, value_when_pressed=False, pull=True)
dpad    = keypad.Keys(dpad_pins,  value_when_pressed=False, pull=True)

axes_pins = {ax: resolve_pin(mapping["axes"][ax]) for ax in mapping["axes"]}
lx = analogio.AnalogIn(axes_pins["LX"])
ly = analogio.AnalogIn(axes_pins["LY"])
rx = analogio.AnalogIn(axes_pins["RX"])
ry = analogio.AnalogIn(axes_pins["RY"])
lt = analogio.AnalogIn(axes_pins["LT"])  # keep triggers fully analog
rt = analogio.AnalogIn(axes_pins["RT"])

# Find our custom HID gamepad (Usage Page 0x01, Usage 0x05), as defined in boot.py
gamepad = None
for d in usb_hid.devices:
    if d.usage_page == 0x01 and d.usage == 0x05:
        gamepad = d
        break
assert gamepad, "No custom HID gamepad found (check boot.py)"

# ---------- Helpers ----------
AXIS_STATE = {}  # stores last smoothed value per axis (for low-pass)
CENTER = 128     # center for 8-bit axes

def read_axis(adc, name):
    # NOTE: AnalogIn.value is always 16-bit (0..65535) regardless of MCU ADC resolution.
    # Shift >> 8 to scale into 8-bit (0..255) because the HID descriptor is 1 byte per axis.
    raw = adc.value >> 8

    # Invert if requested
    if INVERT.get(name, False):
        raw = 255 - raw

    # Trigger calibration (map [min..max] -> [0..255])
    if name in ("LT","RT"):
        minv = TRIG.get(f"{name}_min", 0)
        maxv = TRIG.get(f"{name}_max", 255)
        span = max(1, (maxv - minv))
        raw = int((raw - minv) * 255 / span)
        if raw < 0:   raw = 0
        if raw > 255: raw = 255

    # Deadzone (sticks typically): clamp to center if within threshold
    dz = DEADZONE.get(name, None)
    if dz is not None and abs(raw - CENTER) < dz:
        raw = CENTER

    # Low-pass smoothing (simple EMA): val = (1-a)*prev + a*raw
    a = SMOOTH.get(name, 0.0)
    prev = AXIS_STATE.get(name, raw)
    val = int((1.0 - a) * prev + a * raw)
    AXIS_STATE[name] = val
    return val

def compute_hat(u,d,l,r):
    # 0=U,1=UR,2=R,3=DR,4=D,5=DL,6=L,7=UL,8=center
    if u and not d and not l and not r: return 0
    if u and not d and not l and r:     return 1
    if not u and not d and not l and r: return 2
    if not u and d and not l and r:     return 3
    if not u and d and not l and not r: return 4
    if not u and d and l and not r:     return 5
    if not u and not d and l and not r: return 6
    if u and not d and l and not r:     return 7
    return 8

# ---------- State & report ----------
button_bits = 0
hat = 8  # neutral

def send_report():
    # Pack 9-byte report to match boot.py descriptor:
    # [0,1]=buttons (16 bits), [2]=hat (low nibble), [3..8]=LX,LY,RX,RY,LT,RT
    report = bytearray(9)
    report[0] = button_bits & 0xFF
    report[1] = (button_bits >> 8) & 0xFF
    report[2] = hat & 0x0F
    report[3] = read_axis(lx, "LX")
    report[4] = read_axis(ly, "LY")
    report[5] = read_axis(rx, "RX")
    report[6] = read_axis(ry, "RY")
    report[7] = read_axis(lt, "LT")
    report[8] = read_axis(rt, "RT")
    gamepad.send_report(report)

# ---------- Main loop ----------
while True:
    # Buttons (event-driven): update bitfield only on changes
    ev = buttons.events.get()
    while ev:
        mask = 1 << ev.key_number  # index matches BUTTON_ORDER
        if ev.pressed:
            button_bits |= mask
        else:
            button_bits &= ~mask
        send_report()
        ev = buttons.events.get()

    # D-pad: sample continuously to allow diagonals
    up    = (not dpad.keys[0].value)
    down  = (not dpad.keys[1].value)
    left  = (not dpad.keys[2].value)
    right = (not dpad.keys[3].value)
    new_hat = compute_hat(up, down, left, right)
    if new_hat != hat:
        hat = new_hat
        send_report()

    # Axes (continuous): always poll to keep motion/pressure smooth
    send_report()
    time.sleep(0.01)  # ~100 Hz overall; adjust if you want faster/slower