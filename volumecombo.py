import time
import subprocess
import sys
import select
import RPi.GPIO as GPIO
from smbus2 import SMBus

# ========== CONFIGURATION ==========
BUTTON_UP = 17         # GPIO for Volume Up button
BUTTON_DOWN = 27       # GPIO for Volume Down button
SHDN_GPIO = 16         # TEMP: GPIO for TPA2016 SHDN pin (set back to 22 later)
JACK_SWITCH_GPIO = 23  # GPIO for headphone jack detect switch
DEBOUNCE_TIME = 0.05   # 50ms polling debounce

# TPA2016 I2C Settings
I2C_BUS = 1
TPA2016_I2C_ADDR = 0x58
GAIN_REGISTER = 0x04
AGC_ENABLE_REGISTER = 0x06
CONFIG_REGISTER = 0x01
SOFTWARE_SHUTDOWN_BIT = 1 << 5  # Bit 5 (correct for SWS)
FIXED_GAIN_DB = 0  # 0 dB, set as desired (-28 to +30 dB)

# ========== TPA2016 CONTROL ==========
def db_to_regval(db):
    db = max(-28, min(30, db))
    return int(db + 28)

def disable_agc_and_set_gain():
    with SMBus(I2C_BUS) as bus:
        # Disable AGC
        bus.write_byte_data(TPA2016_I2C_ADDR, AGC_ENABLE_REGISTER, 0)
        print("AGC disabled.")
        # Set fixed gain
        gain_value = db_to_regval(FIXED_GAIN_DB)
        bus.write_byte_data(TPA2016_I2C_ADDR, GAIN_REGISTER, gain_value)
        print(f"Fixed gain set to {FIXED_GAIN_DB} dB (reg value {gain_value})")

# ========== HARDWARE MUTE (SHDN) ==========
def mute_amp():
    GPIO.output(SHDN_GPIO, GPIO.LOW)
    print("Hardware SHDN: LOW (muted/shutdown)")

def unmute_amp():
    GPIO.output(SHDN_GPIO, GPIO.HIGH)
    time.sleep(0.05)  # Give the amp a moment to power up
    disable_agc_and_set_gain()  # Restore settings after power up
    print("Hardware SHDN: HIGH (unmuted)")

# ========== SOFTWARE MUTE (SWS, REG 0x01, BIT 5) ==========
def sws_software_mute():
    with SMBus(I2C_BUS) as bus:
        reg = bus.read_byte_data(TPA2016_I2C_ADDR, CONFIG_REGISTER)
        reg |= SOFTWARE_SHUTDOWN_BIT
        bus.write_byte_data(TPA2016_I2C_ADDR, CONFIG_REGISTER, reg)
        print("SWS Software Shutdown: ON (muted)")

def sws_software_unmute():
    with SMBus(I2C_BUS) as bus:
        reg = bus.read_byte_data(TPA2016_I2C_ADDR, CONFIG_REGISTER)
        reg &= ~SOFTWARE_SHUTDOWN_BIT
        bus.write_byte_data(TPA2016_I2C_ADDR, CONFIG_REGISTER, reg)
        print("SWS Software Shutdown: OFF (unmuted)")
    disable_agc_and_set_gain()  # Re-assert settings just in case

# ========== VOLUME ==========
def volume_up():
    try:
        subprocess.run(['/usr/bin/amixer', '-q', '-c', '0', 'sset', 'Master', '5+', 'unmute'])
        print("Volume UP")
    except Exception as e:
        print(f"Volume UP error: {e}")

def volume_down():
    try:
        subprocess.run(['/usr/bin/amixer', '-q', '-c', '0', 'sset', 'Master', '5-', 'unmute'])
        print("Volume DOWN")
    except Exception as e:
        print(f"Volume DOWN error: {e}")

# ========== BUTTON STATE ==========
def both_buttons_pressed(up, down):
    return up == 0 and down == 0

def key_pressed():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

# ========== KEYBOARD TEST MODE ==========
def keyboard_mode():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SHDN_GPIO, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(JACK_SWITCH_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print("Keyboard test mode enabled.")
    print("Press 'u' for Volume Up, 'd' for Volume Down, 'm' for HW mute toggle (SHDN), 'b' for BOTH buttons (HW mute), 's' for SWS software mute toggle, 'q' to quit.")
    amp_muted = False
    amp_sws_muted = False
    jack_inserted = False
    try:
        while True:
            # Auto mute/unmute on headphone plug (hardware mute)
            jack_state = GPIO.input(JACK_SWITCH_GPIO)
            if jack_state == 0 and not jack_inserted:
                print("Headphone plugged in: muting speakers (HW)")
                if not amp_muted:
                    mute_amp()
                    amp_muted = True
                jack_inserted = True
            elif jack_state == 1 and jack_inserted:
                print("Headphone unplugged: unmuting speakers (HW)")
                if amp_muted:
                    unmute_amp()
                    amp_muted = False
                jack_inserted = False

            if key_pressed():
                key = sys.stdin.read(1)
                if key == 'u':
                    volume_up()
                elif key == 'd':
                    volume_down()
                elif key == 'm' or key == 'b':
                    if amp_muted:
                        unmute_amp()
                        amp_muted = False
                    else:
                        mute_amp()
                        amp_muted = True
                elif key == 's':
                    if amp_sws_muted:
                        sws_software_unmute()
                        amp_sws_muted = False
                    else:
                        sws_software_mute()
                        amp_sws_muted = True
                elif key == 'q':
                    print("Exiting keyboard test mode.")
                    break
            time.sleep(DEBOUNCE_TIME)
    finally:
        GPIO.cleanup()

# ========== GPIO MODE ==========
def gpio_mode():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_UP, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_DOWN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SHDN_GPIO, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(JACK_SWITCH_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    amp_muted = False
    already_triggered = False
    last_up = 1
    last_down = 1
    jack_inserted = False

    try:
        print("GPIO mode: Volume up/down = GPIO 17/27, MUTE toggle = both together. Auto-mute on headphone plug.")
        while True:
            up = GPIO.input(BUTTON_UP)
            down = GPIO.input(BUTTON_DOWN)
            jack_state = GPIO.input(JACK_SWITCH_GPIO)

            # Volume up: Only triggers on transition from high to low (button press)
            if up == 0 and last_up == 1 and down == 1:
                volume_up()
            # Volume down: Only triggers on transition from high to low (button press)
            if down == 0 and last_down == 1 and up == 1:
                volume_down()

            # Combo for mute/unmute (triggers once per combo press, hardware mute)
            if both_buttons_pressed(up, down) and not already_triggered:
                if amp_muted:
                    unmute_amp()
                    amp_muted = False
                else:
                    mute_amp()
                    amp_muted = True
                already_triggered = True
            elif not both_buttons_pressed(up, down):
                already_triggered = False

            # Auto mute/unmute on headphone plug (hardware mute)
            if jack_state == 0 and not jack_inserted:
                print("Headphone plugged in: muting speakers (HW)")
                if not amp_muted:
                    mute_amp()
                    amp_muted = True
                jack_inserted = True
            elif jack_state == 1 and jack_inserted:
                print("Headphone unplugged: unmuting speakers (HW)")
                if amp_muted:
                    unmute_amp()
                    amp_muted = False
                jack_inserted = False

            last_up = up
            last_down = down

            time.sleep(DEBOUNCE_TIME)
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        GPIO.cleanup()

# ========== MAIN ==========
if __name__ == "__main__":
    disable_agc_and_set_gain()  # At startup

    if sys.stdin.isatty():
        mode = input("Select mode: [g]pio or [k]eyboard? ").strip().lower()
        if mode == 'k':
            print("\nNOTE: SHDN_GPIO is currently set to GPIO 16 (change back to 22 later!)\n")
            keyboard_mode()
        else:
            print("\nNOTE: SHDN_GPIO is currently set to GPIO 16 (change back to 22 later!)\n")
            gpio_mode()
    else:
        # If running as a systemd service, default to GPIO mode
        print("No terminal detected, running in GPIO mode (systemd service).")
        print("\nNOTE: SHDN_GPIO is currently set to GPIO 16 (change back to 22 later!)\n")
        gpio_mode()
