# SailUI
Portable sailing instruments

## Hardware
- Raspberry Pi 4 4Gb
- Waveshare Neo8M GPS board
- Waveshare 7inch LCD screen

## Raspberry OS configuration
### Standard RaspberryOS installation
Default graphic installation
### Install and configure InfluxDB and Grafana
https://docs.influxdata.com/influxdb/v1.8/get-started/
https://docs.influxdata.com/telegraf/v1.17/introduction/installation/

### SystemCTL
Then add a systemd service: (/etc/systemd/system/serial2influx.service)

[Unit]
Description=Read GPS output on serial and send location to InfluxDB
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/sailui/sailui_server_multithread.py
Restart=on-failure
RestartSec = "20sec"

[Install]
WantedBy=multi-user.target
