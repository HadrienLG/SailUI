# SailUI
Portable sailing instruments

## Hardware
- Raspberry Pi 4 4Gb
- Waveshare Neo8M GPS board
- Waveshare 7inch LCD screen
- Waveshare Sens Hat (B)

## Raspberry OS configuration

### Standard RaspberryOS installation
Default graphic installation

### Install and configure InfluxDB and Grafana
- https://docs.influxdata.com/influxdb/v1.8/get-started/
- https://docs.influxdata.com/telegraf/v1.17/introduction/installation/

### Python 3 - Depandancies
`sudo pip3 install -r requirements.txt`
Install the depandancies as root solve an issue with busio module when run as systemd service

All librairies for Waveshare Sense Hat are copied in libs/ from:
https://www.waveshare.com/wiki/Sense_HAT_(B)
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
