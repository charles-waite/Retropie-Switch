## RetroPie Config Steps

#### 1. Prepare SD Card
 1. Download Raspberry Pi Imager.
 2. Open Raspberry Pi Imager and select the Pi device you're using.
 3. Select the RetroPie image under "Emulation and Game OS" -> RetroPie -> Select the image for your Pi model.
 4. Select the SD card you're installing RetroPie onto.
 5. Click Edit Settings to configure Wifi settings, hostname (optional), select time zone and keyboard localization, and enable SSH (highly recommended) in the Edit Settings screen. 
 6. Save settings
 7. Then click the Yes button to install RetroPie.
#### 2. Modify boot.txt  
1. Once the install is complete, mount the SD card (if your OS hasn't already)
2. Run: `sudo nano /boot/config.txt` and make the following changes:
3. Disable internal audio: `#dtparam=audio=on`
4. Add this to the end of the file: `dtoverlay=hifiberry-dac`
5. –––ADD MORE HERE–––– 
#### 3. Insert SD into Pi and boot into Retropie 
> [!IMPORTANT] 
>
> **For Pi 3 and 3+ variants:**   
> If Wifi Power management is not disabled, ssh connections will constantly fail, bluetooth will be very flaky and wifi connectivity will be very spotty. Implementing this small fix likely will increase power consumption but is necessary in my case for functioning wifi.
>  
** Disable Wifi Power Management:  **
> 1. SSH into pi once booted. use command: `sudo ssh pi@you.local.ip.address`. default password is `raspberry`
> 
> 2. Create rc.local file in nano using: `sudo nano /etc/rc.local`  
>
> 3. In nano, add this code:
>>```sh
>>    #!/bin/sh -e 
>>    /sbin/iwconfig wlan0 power off 
>>    exit 0
>>    ```
>    
> 4. Save file and exit nano.
>
> 5. Run this command to give script executable permissions:  `sudo chmod 755 /etc/rc.local`
> 6. This script should persist across boots and run automatically to restore functioning wifi.
> 7. Reboot pi with `sudo reboot`.
#### 4. Upgrade Retropie components.
This can be done in the GUI with an attached controller or keyboard or via SSH.
**GUI:**
1. Once RetroPie is booted, scroll to the settings.
2. Choose the RetroPie Setup option.
3. Select "Update" from the menu.
4. This will take a while depending on the Pi model, but it will scan through and update all installed components.

**SSH:**
1. SSH into your pi: `sudo ssh pi@you.local.ip.address`
2. Run `sudo ~/RetroPie-Setup/retropie_setup.sh`
#### 5. Backlight & Ambient light sensor
- Basic command to set brightness: `echo [integer between 0-255] | sudo tee /sys/class/backlight/rpi_backlight/brightness`
- Add integration with planned overlay for volume battery and change to a percentage rather than an integer for UI simplicity
- *Ambient Light sensor is low priority and for future iteration (if at all).*
#### 6. Configure virtual sound card for SoftVolume control.
If your DAC doesn't support ALSA Mixer functions (many don't), you need to setup a system level software control so that you can control system volume.
Raspi Audio has a script that will set this up automatically. You must complete these steps in this order, including the reboots.
1. Run this from SSH: `sudo wget -O - script.raspiaudio.com | bash`
2. Reboot.
3. Test audio with `sudo speaker-test -l5 -c2 -t wav`. You should hear audio output via headphone jack or connected speakers.
4. Reboot.
5. Volume should now be controllable via `alsamixer`.
Confirm this is necessary and if so, that it still works with PCM5102A DAC. Can copy contents of `/etc/asound.conf` file for manually setup code.

#### 6. Setup volume buttons for Master volume and Mute for TPA2016 amp

#### 7. Copy ROMs to SD-Card.

#### 8. (Optional) Set boot splashscreen for correct display resolution
#### 9. (Optional) Install SkyScraper metadata scraper.