# main.py — Pi Switch controller firmware (dynamic from CSV)
import time, board, digitalio, analogio, usb_hid, csv
import json

CONFIG = {}
try:
    with open("config.json","r") as f:
        CONFIG = json.load(f)
except Exception:
    CONFIG = {}

CSV_FILE = "wiring.csv"

# ---- Helpers ----
def _resolve_pin(label):
    label = (label or "").strip()
    # Handles "MOSI (D4)" -> "D4"
    if "(" in label and ")" in label:
        inner = label[label.find("(")+1:label.find(")")]
        if inner in dir(board):
            return getattr(board, inner)
    if label in dir(board):
        return getattr(board, label)
    raise ValueError(f"Unknown pin label: {label}")

def read_csv(path=CSV_FILE):
    buttons, dpad, sticks, trigs = {}, {"Up":None,"Down":None,"Left":None,"Right":None}, {}, {}
    with open(path, "r") as f:
        r = csv.DictReader(f)
        for row in r:
            control = (row.get("Control") or "").strip()
            role = (row.get("Pad Role") or "").strip().lower()
            pin = (row.get("ItsyBitsy Pin") or "").strip()
            if not control or not role or not pin: continue
            if role == "signal":
                if control.startswith("D-Pad"):
                    if "Up" in control: dpad["Up"] = pin
                    if "Down" in control: dpad["Down"] = pin
                    if "Left" in control: dpad["Left"] = pin
                    if "Right" in control: dpad["Right"] = pin
                else:
                    buttons[control.replace("BT-","")] = pin
            elif role == "wiper":
                if "Joystick-Left" in control and "X" in control: sticks["LX"]=pin
                if "Joystick-Left" in control and "Y" in control: sticks["LY"]=pin
                if "Joystick-Right" in control and "X" in control: sticks["RX"]=pin
                if "Joystick-Right" in control and "Y" in control: sticks["RY"]=pin
                if "Trigger-Left" in control: trigs["LT"]=pin
                if "Trigger-Right" in control: trigs["RT"]=pin
    return buttons,dpad,sticks,trigs

# ---- Load wiring ----
BUTTONS, DPAD, STICKS, TRIGGERS = read_csv()

# ---- Init IO ----
btn_ios = []
for name,pin_label in BUTTONS.items():
    p = digitalio.DigitalInOut(_resolve_pin(pin_label))
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP
    btn_ios.append((name,p))

dpad_ios = {}
for k,v in DPAD.items():
    if v:
        io = digitalio.DigitalInOut(_resolve_pin(v))
        io.direction = digitalio.Direction.INPUT
        io.pull = digitalio.Pull.UP
        dpad_ios[k] = io

def _ain(label): return analogio.AnalogIn(_resolve_pin(label)) if label else None
ain = {k:_ain(v) for k,v in STICKS.items() if v}
ain.update({k:_ain(v) for k,v in TRIGGERS.items() if v})

# ---- HID device ----
gp = None
for dev in usb_hid.devices:
    if dev.usage_page==0x01 and dev.usage==0x05:
        gp = dev
assert gp, "HID gamepad not found"

# ---- Helpers ----
def hat_from_dpad(u,d,l,r):
    if u and not d and not l and not r: return 0
    if u and r: return 1
    if r and not u and not d: return 2
    if d and r: return 3
    if d and not r and not l: return 4
    if d and l: return 5
    if l and not d and not u: return 6
    if u and l: return 7
    return 8

def read_axis(a, name=None):
    if not a: return 128
    val = a.value >> 8  # 0–255

    # Invert
    if name and CONFIG.get("invert",{}).get(name, False):
        val = 255 - val

    # Deadzone (for sticks only)
    if name and name in CONFIG.get("deadzone",{}):
        dz = CONFIG["deadzone"][name]
        mid = 128
        if abs(val - mid) < dz:
            val = mid

    # Trigger calibration
    if name in ("LT","RT") and "triggers" in CONFIG:
        tcfg = CONFIG["triggers"]
        lo = tcfg.get(name+"_min",0)
        hi = tcfg.get(name+"_max",255)
        val = max(0,min(255,int((val-lo)/(hi-lo)*255))) if hi>lo else val

    return val

def read_button(io): return 0 if io.value else 1  # active-low

button_order = sorted([nm for nm,_ in btn_ios])

# ---- Main loop ----
while True:
    bits = 0
    for i,name in enumerate(button_order):
        for nm,io in btn_ios:
            if nm==name and read_button(io):
                bits |= (1<<i); break
    u=read_button(dpad_ios.get("Up")) if dpad_ios.get("Up") else 0
    d=read_button(dpad_ios.get("Down")) if dpad_ios.get("Down") else 0
    l=read_button(dpad_ios.get("Left")) if dpad_ios.get("Left") else 0
    r=read_button(dpad_ios.get("Right")) if dpad_ios.get("Right") else 0
    hat=hat_from_dpad(u,d,l,r)
    lx,ly = read_axis(ain.get("LX"),"LX"), read_axis(ain.get("LY"),"LY")
    rx,ry = read_axis(ain.get("RX"),"RX"), read_axis(ain.get("RY"),"RY")
    lt,rt = read_axis(ain.get("LT"),"LT"), read_axis(ain.get("RT"),"RT")
    report = bytes([bits&0xFF,(bits>>8)&0xFF,hat,lx,ly,rx,ry,lt,rt])
    gp.send_report(report)
    time.sleep(0.01)