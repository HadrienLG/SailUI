# SailUI
Portable sailing instruments

## Hardware
- Raspberry Pi 4 4Gb
- Waveshare Neo8M GPS board
- Waveshare 7inch LCD screen

## Raspberry OS configuration
First, install and configure InfluxDB and Grafana
Then add a systemd service: (/etc/systemd/system/serial2influx.service)

[Unit]
Description=Read GPS output on serial and send location to InfluxDB
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/pi/sailui/serial2influxdb_position.py
Restart=on-failure
RestartSec = "20sec"

[Install]
WantedBy=multi-user.target
