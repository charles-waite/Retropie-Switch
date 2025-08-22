import time, json, board, digitalio, analogio

PINMAP_FILE = "button-pinout.json"
CONFIG_FILE = "config.json"

BAR_WIDTH = 32
UPDATE_HZ = 5

def _resolve_pin(label):
    label = (label or "").strip()
    if "(" in label and ")" in label:
        inner = label[label.find("(")+1:label.find(")")]
        if inner in dir(board):
            return getattr(board, inner)
    if label in dir(board):
        return getattr(board, label)
    raise ValueError("Unknown pin label: {}".format(label))

def _load_json(path, default=None):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return default

# ---- Load mappings ----
mapping = _load_json(PINMAP_FILE, {})
BUTTONS = mapping.get("buttons", {})
DPAD    = mapping.get("dpad", {})
AXES    = mapping.get("axes", {})

config  = _load_json(CONFIG_FILE, {})
INV     = config.get("invert", {})
DZ      = config.get("deadzone", {})
TCFG    = config.get("triggers", {})

# ---- Setup I/O ----
btn_ios = []
for name, pin_label in BUTTONS.items():
    p = digitalio.DigitalInOut(_resolve_pin(pin_label))
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP
    btn_ios.append((name, p))

dpad_ios = {}
for k in ("Up", "Down", "Left", "Right"):
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

# ---- Helpers ----
def read_button(io):
    return 0 if io.value else 1  # active-low

def axis_calibrated(name, ain_obj):
    if not ain_obj:
        return None
    val = ain_obj.value >> 8  # 0..255
    # invert
    if INV.get(name, False):
        val = 255 - val
    # deadzone for sticks
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

def bar(val, width=BAR_WIDTH, lo=0, hi=255, center=None):
    if val is None:
        return "-" * width
    val = max(lo, min(hi, val))
    if center is None:
        filled = int((val - lo) * width / float(hi - lo + 1))
        return "#" * filled + "." * (width - filled)
    # centered bar
    left = int(max(0, (center - val) * width / (2.0 * (center - lo + 1))))
    right = int(max(0, (val - center) * width / (2.0 * (hi - center + 1))))
    return "<" * left + "|" + ">" * right + "." * (width - (left + right + 1))

print("Diagnostics using {} + {} ({} Hz)".format(PINMAP_FILE, CONFIG_FILE, UPDATE_HZ))
period = 1.0 / float(UPDATE_HZ)

while True:
    btn_states = {nm: read_button(io) for nm, io in btn_ios}
    dpad_states = {k: read_button(io) for k, io in dpad_ios.items()}
    axes = {k: axis_calibrated(k, ain.get(k)) for k in ain.keys()}

    print("Buttons:", btn_states)
    print("DPad:", dpad_states)
    print("Axes:", axes)

    if "LX" in axes: print("LX {:3d} [{}]".format(axes["LX"], bar(axes["LX"], center=128)))
    if "LY" in axes: print("LY {:3d} [{}]".format(axes["LY"], bar(axes["LY"], center=128)))
    if "RX" in axes: print("RX {:3d} [{}]".format(axes["RX"], bar(axes["RX"], center=128)))
    if "RY" in axes: print("RY {:3d} [{}]".format(axes["RY"], bar(axes["RY"], center=128)))
    if "LT" in axes: print("LT {:3d} [{}]".format(axes["LT"], bar(axes["LT"])))
    if "RT" in axes: print("RT {:3d} [{}]".format(axes["RT"], bar(axes["RT"])))

    up = "^" if dpad_states.get("Up") else "."
    dn = "v" if dpad_states.get("Down") else "."
    lf = "<" if dpad_states.get("Left") else "."
    rt = ">" if dpad_states.get("Right") else "."
    print("DPad [{}{}{}{}]".format(lf, up, dn, rt))

    print("-" * (BAR_WIDTH + 20))
    time.sleep(period)