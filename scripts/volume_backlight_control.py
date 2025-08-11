#!/usr/bin/env python3
"""
Raspberry Pi 3A+ script for Retropie:
- Volume up/down via two GPIO buttons
- Toggle amp shutdown (mute) when both are pressed
- Headphone jack detection mutes amp
- OSD volume/mute/headphone status (blocky bar + pixel font)
- Backlight adjust via Combined Joy-Con (Home + d-pad up/down)

Dependencies:
  sudo pip3 install adafruit-circuitpython-tpa2016 pygame evdev
  Place a retro pixel TTF (e.g. Jersey10.ttf) alongside this script.

Run at startup (e.g. in /etc/rc.local or crontab @reboot).
"""
import time
import re
import subprocess
import threading
import os

import board, busio, digitalio, adafruit_tpa2016
import pygame
from evdev import InputDevice, list_devices, ecodes

# ─── CONFIG ────────────────────────────────────────────────────────────────────
VOL_UP_PIN    = 17    # BCM 17
VOL_DOWN_PIN  = 27    # BCM 27
HP_DETECT_PIN = 23    # BCM 23

OSD_FONT_PATH   = "./Jersey10.ttf"
OSD_FONT_SIZE   = 24
OSD_BAR_CHUNKS  = 10
OSD_WIDTH       = 800
OSD_HEIGHT      = 480

VOLUME_STEP     = 5     # % per press
BACKLIGHT_STEP  = 16    # 0-255 increment
BACKLIGHT_PATH  = "/sys/class/backlight"

# ─── INIT HARDWARE ─────────────────────────────────────────────────────────────
# I2C + TPA2016 amplifier
i2c = busio.I2C(board.SCL, board.SDA)
amp = adafruit_tpa2016.TPA2016(i2c)

# GPIO inputs (internal pull-ups, switches pull to GND)
def make_input(pin):
    d = digitalio.DigitalInOut(getattr(board, f"GPIO{pin}"))
    d.direction = digitalio.Direction.INPUT
    d.pull = digitalio.Pull.UP
    return d

btn_up    = make_input(VOL_UP_PIN)
btn_down  = make_input(VOL_DOWN_PIN)
hp_detect = make_input(HP_DETECT_PIN)

# ─── OSD SETUP ─────────────────────────────────────────────────────────────────
os.environ["SDL_VIDEODRIVER"] = "fbcon"
pygame.init()
screen = pygame.display.set_mode((OSD_WIDTH, OSD_HEIGHT), pygame.FULLSCREEN)
font   = pygame.font.Font(OSD_FONT_PATH, OSD_FONT_SIZE)

def draw_osd(volume, muted, hp_inserted):
    screen.fill((0,0,0))
    title = "HEADPHONES" if hp_inserted else ("MUTED" if muted else "VOLUME")
    lbl = font.render(title, True, (255,255,255))
    screen.blit(lbl, (20,20))
    chunks  = int((volume/100) * OSD_BAR_CHUNKS)
    chunk_w = 600 // OSD_BAR_CHUNKS
    for i in range(OSD_BAR_CHUNKS):
        rect = pygame.Rect(20 + i*chunk_w, 60, chunk_w-2, 30)
        color = (255,255,255) if (i < chunks and not muted) else (60,60,60)
        pygame.draw.rect(screen, color, rect)
    pygame.display.update()

# ─── VOLUME HELPERS ────────────────────────────────────────────────────────────
vol_lock = threading.Lock()
def change_volume(delta):
    with vol_lock:
        subprocess.run([
            "amixer", "-qc", "0", "sset", "Master",
            f"{abs(delta)}{'+' if delta>0 else '-'}", "unmute"
        ])

def get_volume():
    raw = subprocess.check_output([
        "amixer", "-qc", "0", "sget", "Master"
    ]).decode(errors="ignore")
    m = re.search(r"(\d+)%", raw)
    return int(m.group(1)) if m else 0

# ─── BACKLIGHT HELPERS ─────────────────────────────────────────────────────────
def _find_backlight_file():
    for d in os.listdir(BACKLIGHT_PATH):
        p = os.path.join(BACKLIGHT_PATH, d, "brightness")
        if os.path.isfile(p):
            return p
    raise RuntimeError("No backlight brightness file found")
BL_FILE = _find_backlight_file()

def get_backlight():
    with open(BL_FILE) as f:
        return int(f.read().strip())

def adjust_backlight(delta):
    curr = get_backlight()
    new  = max(0, min(255, curr + delta))
    subprocess.run(
        ["sudo", "tee", BL_FILE],
        input=str(new).encode(),
        stdout=subprocess.DEVNULL
    )
    return new

# ─── MAIN BUTTON LOOP ───────────────────────────────────────────────────────────
mute_state = False
def update_amp_shutdown():
    # headphone override
    if not hp_detect.value:
        amp.shutdown = True
    else:
        amp.shutdown = mute_state

def button_loop():
    global mute_state
    last_u, last_d, last_hp = True, True, True
    while True:
        u, d, hp = btn_up.value, btn_down.value, hp_detect.value
        # headphone inserted/removed
        if hp != last_hp:
            last_hp = hp
            update_amp_shutdown()
            draw_osd(get_volume(), mute_state, not hp)
        # both pressed -> toggle mute
        if not u and not d and (last_u or last_d):
            mute_state = not mute_state
            update_amp_shutdown()
            draw_osd(get_volume(), mute_state, not hp)
        # vol up
        if not u and last_u:
            change_volume(+VOLUME_STEP)
            draw_osd(get_volume(), mute_state, not hp)
        # vol down
        if not d and last_d:
            change_volume(-VOLUME_STEP)
            draw_osd(get_volume(), mute_state, not hp)
        last_u, last_d = u, d
        time.sleep(0.05)

# ─── JOYCON BACKLIGHT WATCHER ─────────────────────────────────────────────────
home_pressed = False
def find_combined_joycon():
    for fn in list_devices():
        dev = InputDevice(fn)
        if 'Joy-Con' in dev.name or 'joycond' in dev.name:
            return dev
    raise RuntimeError("Combined Joy-Con device not found")

def joycon_watcher():
    global home_pressed
    dev = find_combined_joycon()
    for e in dev.read_loop():
        # Home button toggle
        if e.type == ecodes.EV_KEY and e.code == ecodes.KEY_HOME:
            home_pressed = (e.value == 1)
        # D-pad up/down while Home held
        if home_pressed and e.type == ecodes.EV_ABS and e.code == ecodes.ABS_HAT0Y and e.value != 0:
            if e.value == -1:
                adjust_backlight(+BACKLIGHT_STEP)
            elif e.value == 1:
                adjust_backlight(-BACKLIGHT_STEP)
            draw_osd(get_volume(), mute_state, not hp_detect.value)

# ─── STARTUP ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    update_amp_shutdown()
    threading.Thread(target=button_loop, daemon=True).start()
    threading.Thread(target=joycon_watcher, daemon=True).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pygame.quit()
