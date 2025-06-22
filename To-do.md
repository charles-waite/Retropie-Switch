To-do:

- [ ] Design v1 Case

  ​	Just a POC, can be blocky and doesn't need mounting points for hardware, just space for things to fit. I can use this to mark out where components can mount 

  ​	Clamshell design in 2 layers: screen bezel, rear case, access port for Pi

  ​	Mounts include: 

  ​		• Speakers

  ​		• Amp board

  ​		• Headphone Jack (should get a mountable version, breadboard one isnt ideal)

  ​		• DAC (needs to be really secure to handle GPIO insertion and removal)

  ​		• Buttons w/ rocker switch pieces

  ​		• USB ports

  ​		• Joycon Rails

  ​		• Joycon controller board

  ​		• Battery	

- [ ] Integrate buttons for volume, power, etc

- [ ] Upgrade to PiSugar 3Plus to get power on/off

- [ ] Integrate a USB hub: 2 data ports external, one internal for Joycons.

  ​	• Maybe find a USB hub at home and scavenge it?

  ​	• Minimum 3 ports

- [ ] Install a header shim to double the 2x20 ports for more seamless connection for buttons, audio amp, usb, etc

- [ ] Consider a [short female header](https://www.adafruit.com/product/2243) for the DAC to save space (may not work with the gpio shim, maybe stack them and solder together?)

- [ ] Setup and test Volume mute button code w/ auto-mute on headphone insertion.

  ​	• Wire up headphone switch to GPIO to trigger automatic mute (Inner pins are open when headphones are inserted, DAC supports this)

- [ ] Setup Backlight control script and test with Joycons.

- [x] Create Github Repo

- [ ] Create installer/setup script

  - [ ] Creates and registers system services and runs them at boot
  - [ ] Links services to correct locations (would be /home/pi/*REPO-NAME*)
  - [ ] installs scripts to correct directories
  - [ ] Create update script that pulls new scripts and restarts systemctl and services

- [ ] Refactor script to use Adafruit python libraries (since ChatGPT keeps fucking up the registers and forgetting functionality)
