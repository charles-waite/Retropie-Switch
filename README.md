# Raspberry Switch

A handheld, modular, Raspberry Pi-based game console inspired by the Nintendo Switch.  
Designed for RetroPie gaming, open-source hacking, and custom hardware add-ons—housed in a 3D-printed case with real Switch Joycons and tailored for hardware tinkerers.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Hardware List](#hardware-list)
- [Case & Design Notes](#case--design-notes)
- [Joycon Rail Connector](#joycon-rail-connector)
- [To-Do](#to-do)
- [Setup & Install Instructions](#setup--install-instructions)
- [Development Roadmap](#development-roadmap)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Project Overview

**Raspberry Switch** is a DIY handheld gaming console based on the Raspberry Pi 3A+, with a 7" touchscreen, true Joycon compatibility, built-in audio, battery power, and an open 3D-printed enclosure.  
This project aims to be a “Switch-like” device running RetroPie, with modular Python scripts handling hardware functions like backlight, volume, overlay, battery status, and LED indicators.

All hardware and software designs are eventually intended to be open-sourced for others to build, adapt, and contribute.

---

## Features

- RetroPie-based, runs classic games on a handheld Pi
- 3D-printed clamshell case with access panels
- Real Nintendo Switch Joycon rails for detachable controls
- USB-C charging with PiSugar UPS and battery support
- 7” touchscreen display with adjustable backlight (including auto-brightness)
- Custom volume controls (including hardware mute and OSD overlay)
- Stereo amp and speakers (with mini DAC for high-quality audio)
- Headphone jack with auto-mute detection
- On-screen overlays for status and actions
- Status LEDs for power, charging, and battery
- Expandable via internal USB hub for extra controllers/devices
- Open design—schematics, scripts, and CAD files included

---

## Hardware List

- Raspberry Pi 3A+
- PiSugar 3 Plus (battery/UPS)
- 7” Touchscreen display
- Switch Joycon rails (or donor Joycon charger for rails/connector)
- Joycons
- Tiny stereo speakers
- Mini DAC (generic PCM5102A variant)
- Small hardware buttons (power, volume, etc.)
- USB-C charging input relocated/extended from PiSugar
- Liquid flux

---

## Progress pictures

![Display Stand Side](/resources/Display stand Side.jpeg)
![Board Sandwich](/resources/Board sandwich - Display, PiSugar, Pi 3A+.jpeg)


---

## Case & Design Notes

- Custom 3D-printed, clamshell design in two layers (screen bezel, rear case)
- Mounts for all internal components (speakers, amp, DAC, buttons, USB, Joycon rails)
- Foam or adhesive for clean fit to screen
- Mounts directly to LCD panel studs for a robust build

---

## To-Do

- [ ] **Design v1 case** (simple POC, clamshell, access ports)
    - Mounts for speakers, amp, headphone jack, DAC, buttons, USB, Joycon rails, controller board, battery
- [ ] **Integrate buttons** for volume, power, etc.
- [ ] **Upgrade to PiSugar 3 Plus** for power management
- [ ] **Add internal USB hub** (minimum 3 ports: 2 external, 1 internal for Joycons)
- [ ] **Optimize DAC mounting** for durability and space
- [ ] **Setup & test volume/mute buttons**, with auto-mute on headphone insertion
- [ ] **Setup backlight control script**, test with Joycons
- [x] **Create GitHub repo**
- [ ] **Create installer/setup script**
    - [ ] Registers system services at boot
    - [ ] Links scripts and services correctly
    - [ ] Includes update script for pulling changes & restarting services
- [ ] **Refactor scripts** to use Adafruit libraries for reliability
- [ ] **Determine ribbon cable orientation for Joycon rails**
- [x] **Design Joycon Rail cable extender and breakout board variants**
- [ ] **Design custom slider rails using a 4-pin connector to carry VIN/GND + I2C signal**
	- 	Could use a Magnetic "MagSafe" style plug, USB-C plugs, or something like a card edge connector.

---

## Setup & Install Instructions

### 1. Prepare SD Card

- Download and flash the RetroPie IMG to your SD card, or
- Install Raspbian 64-bit Lite (Bookworm) to SD

> **Note for Pi 3/3+:**  
> - Disable WiFi Power Management:  
>   Edit `/etc/rc.local` and add:  
>   ```sh
>   /sbin/iwconfig wlan0 power off
>   exit 0
>   ```
>   Run: `sudo chmod 755 /etc/rc.local`
> - Follow [raspberrypi5-retropie-setup instructions](https://github.com/danielfreer/raspberrypi5-retropie-setup)

### 2. Boot Configuration

- Edit `boot.txt`, comment out `#dtparam=audio=on`
- (Double-check these steps for Bookworm compatibility)

### 3. System Updates

- `sudo apt-get update`
- `sudo apt-get upgrade`
- Boot into RetroPie, run system updates

### 4. Audio & Volume Controls

- Configure virtual sound card for SoftVolume control
- Set up hardware volume/mute buttons and OSD overlay
- Integrate auto-mute on headphone detection (using headphone jack GPIO switch)

### 5. Backlight & Sensor

- Connect and script ambient light sensor to GPIO for auto backlight
- Connect LCD backlight control to GPIO/PWM pin

### 6. Joycon Rails

- Wire rails using Molex ribbon cables per plan above
- Test fit for correct cable orientation and slot routing

### 7. Installer Script (planned)

- Run installer script to set up services and scripts at boot
- Update script for future improvements

---

## Development Roadmap

- Modular Python scripts for backlight, volume, overlay, battery, and status LEDs
- Hardware abstraction to allow swapping components (DAC, screen, battery, etc.)
- Easy-to-follow setup and assembly documentation (including CAD files and images)
- Comprehensive OSD overlay for quick status/config access
- Plug-and-play Joycon integration
- Planned public open-source release when project reaches v1.0

---

## License

*To be added upon public release. Consider using [MIT](https://choosealicense.com/licenses/mit/) or [GPLv3](https://choosealicense.com/licenses/gpl-3.0/) license.*

---

## Acknowledgments

- Inspired by the Nintendo Switch, RetroPie, and countless open-source handheld projects

---

## Contributing

*Contributions, feedback, and hardware test reports are welcome! Please open issues or pull requests once the repo is public.*

---

## Contact

Project lead: charles-waite  
For questions, suggestions, or to get involved, open an issue.

---