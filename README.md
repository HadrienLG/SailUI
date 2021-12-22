# SailUI

Portable sailing instruments

## Ambition
Pouvoir avoir un minimum d'instrumentation quand on change de bateau à chaque navigation

## Kit de base, actuel
Un raspberry pi 4 avec un HAT GPS Neo8M et un HAT Sensor B

## Mise en route
Utiliser le script *installation.sh* à partir d'une carte SD avec RaspiOS

## Configuration du HAT GPS
Depuis un ordinateur avec Windows, télécharger ucenter depuis u-blox.com et l'installer.
Télécharger et installer les pilotes SiliconLabs CP210X USB to UART depuis silabs.com

Brancher le HAT au pc avec un cable USB après avoir placé les jumpers sur A (USB GNSS), ouvrir ucenter et choisir le port COM associé.
Ouvrir *View\Configuration View*
Aller au menu *PRT (Ports)*. En bas à gauche, ouvrir le cadenas avec un clic, cliquer sur Poll pour appeler les paramètres en cours, modifier la valeur de *Baudrates* à *57600* puis cliquer sur *Send*.
Aller au menu *RATE (Rates)* et changer la *Measurement Period* pour obtenir le taux de rafraichissement désiré (200ms = 5Hz, 100ms = 10Hz). Cliquer sur *Send*.
Aller au menu *CFG (Configuration)* et choisir *Devices* *2-I2C-EEPROM*, *Save current configuration* et cliquer sur *Send*.
[Inspiré de https://dadfpv.com/how-to-configure-optimal-gps-settings-increase-update-rate-sam-m8q-m8q-5883-and-similar-ublox-based/]

Sinon, utilisation en ligne de commande de l'outil ubxtool (https://gpsd.io/ubxtool-examples.html) qui vient avec gpsd-clients

Pour mettre à jour l'horloge interne à l'aide du GPS, utiliser la fonction PPS dans GPSD pour avoir un ntp

------------------------------

## Hardware

SERVER

- Raspberry Pi 4 4Gb
- Waveshare Neo8M GPS board
- Waveshare 7inch LCD screen

- Waveshare Sens Hat (B)
  - ICM20948: (3-axis accelerometer, 3-axis gyroscope, and 3-axis magnetometer), detects movement, orientation, and magnetic
  - SHTC3: digital temperature and humidity sensor
  - LPS22HB: barometric pressure sensor

MODULES

- Inkplate 6 : 800x600 epaper screen (6")

- Adafruit HUZZAH32 – ESP32 Feather Board with TFT FeatherWing - 2.4" 320x240 Touchscreen (PID 3591 and 3315)
TFT_CS is pin #15, TFT_DC is pin #33
RT is pin #32 (touch screen)
SD is pin #14

- M5Stack Fire : ESP32 IP5306 MPU6886 BMM150 MICPHONE, LCD 320x240 color ILI9342C (2")
PINout
  - LCD & TF card
| ESP32 Chip | GPIO23    | GPIO19 | GPIO18 | GPIO14 | GPIO27 | GPIO33 | GPIO32 | GPIO4 |
|------------|-----------|--------|--------|--------|--------|--------|--------|-------|
| ILI9342C   | MOSI/MISO | /      | CLK    | CS     | DC     | RST    | BL     |       |
| TF Card    | MOSI      | MISO   | CLK    |        |        |        |        | CS    |
  - Button & Speaker
| ESP32 Chip | GPIO39   | GPIO38   | GPIO37   | GPIO25      |
|------------|----------|----------|----------|-------------|
| Button Pin | BUTTON A | BUTTON B | BUTTON C | /           |
| Speaker    |          |          |          | Speaker Pin |
  - GROVE Port A & IP5306 => I2C address is 0x75
| ESP32 Chip | GPIO22 | GPIO21 | 5V | GND |
|------------|--------|--------|----|-----|
| GROVE A    | SCL    | SDA    | 5V | GND |
| IP5306     | SCL    | SDA    | 5V | GND |
IP5306 charging/discharging，Voltage parameter
|       charging       |      discharging     |
|:--------------------:|:--------------------:|
| 0.00 ~ 3.40V -> 0%   | 4.20 ~ 4.07V -> 100% |
| 3.40 ~ 3.61V -> 25%  | 4.07 ~ 3.81V -> 75%  |
| 3.61 ~ 3.88V -> 50%  | 3.81 ~ 3.55V -> 50%  |
| 3.88 ~ 4.12V -> 75%  | 3.55 ~ 3.33V -> 25%  |
| 4.12 ~   /   -> 100% | 3.33 ~ 0.00V -> 0%   |
  - 6-Axis MotionTracking Sensor MPU6886, I2C address 0x68
| ESP32 Chip | GPIO22 | GPIO21 | 5V | GND |
|------------|--------|--------|----|-----|
| MPU6886    | SCL    | SDA    | 5V | GND |
  - 3-Axis Geomagnetic Sensor BMM150, I2C address 0x10
| ESP32 Chip | GPIO22 | GPIO21 | 5V | GND |
|------------|--------|--------|----|-----|
| BMM150     | SCL    | SDA    | 5V | GND |
  - LED Bar & Micphone & Speaker
| ESP32 Chip | GPIO15  | GPIO34  | GPIO25       |
|------------|---------|---------|--------------|
| Hardwares  | SIG Pin | MIC Pin |  Speaker Pin |

- M5StickC PLUS : ESP32 AXP192 MPU6886, LCD 240x135 px (1.14") ST7789v2, MIC SPM1423
  - RED LED & IR Transmitter & BUTTON A & BUTTON B
| ESP32          | GPIO10  | GPIO9           | GPIO37     | GPIO39     | GPIO2      |
|----------------|---------|-----------------|------------|------------|------------|
| RED LED        | LED Pin |                 |            |            |            |
| IR Transmitter |         | Transmitter Pin |            |            |            |
| BUTTON A       |         |                 | Button Pin |            |            |
| BUTTON B       |         |                 |            | Button Pin |            |
| Buzzer         |         |                 |            |            | Buzzer Pin |

  - TFT LCD, ST7789v2 (135x240)
| ESP32   | GPIO15   | GPIO13  | GPIO23 | GPIO18  | GPIO5  |
|---------|----------|---------|--------|---------|--------|
| TFT LCD | TFT_MOSI | TFT_CLK | TFT_DC | TFT_RST | TFT_CS |

  - GROVE PORT
| ESP32      | GPIO33 | GPIO32 | 5V | GND |
|------------|--------|--------|----|-----|
| GROVE port | SCL    | SDA    | 5V | GND |

  - MIC (SPM1423)
| ESP32    | GPIO0 | GPIO34 |
|----------|-------|--------|
| MICPHONE | CLK   | DATA   |

  - 6-Axis posture sensor (MPU6886) & power management IC (AXP192)
| ESP32               | GPIO22 | GPIO21 |
|---------------------|--------|--------|
| 6-Axis IMU sensor   | SCL    | SDA    |
| Power management IC | SCL    | SDA    |

  - AXP192
| Microphone |  RTC | TFT backlight | TFT IC | ESP32/3.3V MPU6886 | 5V GROVE |
|:----------:|:----:|:-------------:|:------:|:------------------:|:--------:|
|   LDOio0   | LDO1 |      LDO2     |  LDO3  |       DC-DC1       |  IPSOUT  |

## Raspberry OS configuration

### Standard RaspberryOS installation

Default graphic installation

### Install and configure InfluxDB and Grafana

- <https://docs.influxdata.com/influxdb/v1.8/get-started/>
- <https://docs.influxdata.com/telegraf/v1.17/introduction/installation/>

### Python 3 - Depandancies

`sudo pip3 install -r requirements.txt`

Install the depandancies as root solve an issue with busio module when run as systemd service

All librairies for Waveshare Sense Hat are copied in libs/ from:
<https://www.waveshare.com/wiki/Sense_HAT_(B>)

Some adjustements have been made to run them easily in threads

### SystemCTL

To run the server from boot:
`cp sailui_server.service /lib/systemd/system/sailui_server.service`

Reload systemd daemon
`sudo systemctl daemon-reload`

And enable your new service
`sudo systemctl enable sailui_server.service`

You can check the service's status:
`sudo systemctl status sailui_server.service`

Or see the journal:
`journalctl -u sailui_server.service`

### Autostart

To run Chrome at startup, edit
'sudo nano /home/pi/.config/lxsession/LXDE-pi/autostart'

And add:
@chromium-browser --start-fullscreen --start-maximized http://localhost:1880/ui


