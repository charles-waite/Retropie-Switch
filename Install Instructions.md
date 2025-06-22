## RetroPie Config Steps

#### 1. Prepare SD Card

Download Retropie IMG and flash to SD (skip to step 2). 

—OR—  

Install Raspbian 64-bit Lite (Bookworm) onto SD  

> [!IMPORTANT] 
>
> **ONLY IF USNG PI 3/3+:**   
>
> 1. Disable Wifi Power Management:  
>    `sudo nano /etc/rc.local`  
>
> 2. Add:   
>
>    ```sh
>    #!/bin/sh -e 
>    /sbin/iwconfig wlan0 power off 
>    exit 0
>    ```
>
> 3. Then run this command:  `sudo chmod 755 /etc/rc.local`
>
> 4. Configure OS according to these instructions: [raspberrypi5-retropie-setup](https://github.com/danielfreer/raspberrypi5-retropie-setup)  
>    (This can take a few hours to complete)



#### 2. Modify boot.txt  

​      Comment out: `#dtparam=audio=on`  
–––ADD MORE HERE––––  
DOUBLE CHECK THAT THESE WORK/ARE NECESSARY ON BOOKWORM

#### 3. Run `sudo apt-get update` then run `sudo apt-get upgrade`

#### 4. Boot into Retropie and run any updates

#### 5. Configure virtual sound card for SoftVolume control.

#### 6. Setup volume buttons for Master volume and Mute for TPA2016 speakers:
- Install script: 