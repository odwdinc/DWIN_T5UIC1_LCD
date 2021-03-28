# DWIN_T5UIC1_LCD

## Python class for the Ender 3 V2 LCD and klipper3d with OctoPrint

https://www.klipper3d.org
https://octoprint.org/


## Setup:

### [Disable Linux serial console](https://www.raspberrypi.org/documentation/configuration/uart.md)
  By default, the primary UART is assigned to the Linux console. If you wish to use the primary UART for other purposes, you must reconfigure Raspberry Pi OS. This can be done by using raspi-config:

  * Start raspi-config: `sudo raspi-config.`
  * Select option 3 - Interface Options.
  * Select option P6 - Serial Port.
  * At the prompt Would you like a login shell to be accessible over serial? answer 'No'
  * At the prompt Would you like the serial port hardware to be enabled? answer 'Yes'
  * Exit raspi-config and reboot the Pi for changes to take effect.
  
  For full instructions on how to use Device Tree overlays see [this page](https://www.raspberrypi.org/documentation/configuration/device-tree.md). 
  
  In brief, add a line to the `/boot/config.txt` file to apply a Device Tree overlay.
    
    dtoverlay=disable-bt

### [Enabling Klipper's API socket](https://www.klipper3d.org/API_Server.html)
  By default, the Klipper's API socket is not enabled. In order to use the API server, the file /etc/default/klipper need to be updated form

    KLIPPY_ARGS="/home/pi/klipper/klippy/klippy.py /home/pi/printer.cfg -l /tmp/klippy.log"
To:

    KLIPPY_ARGS="/home/pi/klipper/klippy/klippy.py /home/pi/printer.cfg -a /tmp/klippy_uds -l /tmp/klippy.log"


## Useage:

### Wire the display 
  Display <-> Raspberry Pi 
  Rx  =   14  (Tx)
  Tx  =   15  (Rx)
  Ent =   13
  A   =   19
  B   =   26
  Vcc =   2   (5v)
  Gnd =   6   (GND)

### Run The Code

```python
#!/usr/bin/env python3
from dwinlcd import DWIN_LCD

encoder_Pins = (26, 19)
button_Pin = 13
LCD_COM_Port = '/dev/ttyAMA0'
OctoPrint_API_Key = 'XXXXXX'

DWINLCD = DWIN_LCD(
	LCD_COM_Port,
	encoder_Pins,
	button_Pin,
	OctoPrint_API_Key
)
```

# Status:

## Working:

 Print Menu:
 
    * List / Print jobs from OctoPrint
    * Auto swiching forom to Print Menu on job start / end.
    * Display Print time, Progress, Temps, and Job name.
    * Pause / Resume / Cancle Job
    * Tune Menu: Print speed and Temps

 Perpare Menu:
 
    * Move / Jog toolhead
    * Disable stepper
    * Auto Home
    * Preheat
    * cooldown
 
 Info Menu
 
    * Shows printer info.

## Notworking:

    * z offset
    * Save / Loding Preheat setting, hardcode on start can be changed in menu but will not retane on restart.
    * The Control: Motion Menu
