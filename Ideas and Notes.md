**Raspberry Switch**



**Ideas:**



**A RetroPie-based Switch clone**

3D Printed Case (custom or using existing design as template)

- Built-in RPi 3A + Battery/UPS + Stereo Amp + Speakers
- Switch Joycon rails wired to charge joycons
- Removable back panel for access to Pi
- Mounts to lcd panel studs
- Gasket/adhesive for clean fit to screen

Ergo-Grips for real Joycons

- Or 3rd Party Ergo Joycon replacements with switch rails
- May need a premade joycon charger to pillage parts from

RetroPie

7” Touchscreen

Relocated Headphone Jack

USB-C charging jack on top or side wired to battery/UPS

Power Button

Volume buttons (or figure out OSD solution)

v2 - External HDMI port (hdmi over usbc?)



**Parts List:**

Pi 3 A+

PiSugar 3 Plus

7” Touchscreen

Switch Side rails -OR- Joycon charger to pillage 

Joycons

Tiny Stereo Speakers

Small buttons for power/volume

USB-C connector

Small gauge wires

Liquid flux

Small gauge solder



**Plan for joycon:**

- Scavenge board and rails from charging joycon
- Solder tiny wires to rail ribbon cable to extend connection to board from far sides
- Should work with *Joycond* out of the box via USB
- Connect to USB bus with wires rather than connector



**Plan for audio**

- BT audio is a non-starter for now
- Use mini DAC 
- Setup SoftVol to control volume to DAC
- Wire speaker amp to rca output pads on DAC
- Use I2C gain controls on amp to turn it all the way down when both volume buttons are pressed (this will functionally work as a mute switch too)
  - Need to figure out button combos and long press for this to work properly.
- Pressing both buttons again restores the gain value back to a specified setting.
- Maybe switch volume controls to be more logarithmic?



**Design a popup menu for custom actions to be run**

- Could be used to manually mute audio or run scripts to make basic config changes.



**Ambient light sensor for backlight**

Automate backlight brightness using a photocell.

- Can use a cheap phototransistor tied to gpio.
- LCD Backlight can be connected to GPIO-PWM pin and controlled with code
- Could find a script that will monitor that pin and change the output accordingly.



**Space for Audio stuff**

- Mount to lid
- DAC uses gpio header
- Amp is wired to DAC and gets power from GPIO



**USB**

Do I even need more than one? 

- Loading roms over USB
- Secondary controllers? 
- Internal hub (adafruit breakout board) with an externally accessible port or two?



**Status LEDs**

(Tested with adafruit 5mm LEDs https://www.adafruit.com/product/4203)

Green = 220 Ω

Blue = 4,700 Ω

Red = 2,200 Ω

This may differ when I try 3mm ones. Or I could do RGB using a software PWM and a 4-pin RGB LED.