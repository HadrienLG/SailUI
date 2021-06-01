# encoding: utf8
"""
SailUI - GPS data from serial port parsed and send to InfluxDB

MIT License

Copyright (c) 2021 HadrienLG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import subprocess
import logging
import time

from subprocess import check_call

import config.hardware as hardware
from libs.LEDplus import LEDplus
from gpiozero import Button, LED

def shutdown():
    logging.info('Extinction demandée')
    check_call(['sudo', 'poweroff'])

if __name__ == "__main__":
    # Initialisation
    logging.basicConfig(filename='sailui_monitor.log', level=logging.DEBUG)
    logging.info('Démarrage de SailUI-Monitor, début de journalisation')
    
    powerLED = LEDplus(hardware.leds['power'])
    powerLED.on()
    
    red = LEDplus(hardware.leds['red'])
    
    powerB = Button(hardware.buttons['power'], hold_time=5) # Si appui 5sec
    powerB.when_held = shutdown # Alors déclenchement du signal d'arrêt

    # Vérification des status des services systemd
    mes_services = ['sailui_publish_gps.service', 'sailui_publish_sensors.service']
    while True:
        time.sleep(5) # Toutes les 20 secondes
        for service in mes_services:
            p =  subprocess.Popen(["systemctl", "status", service], stdout=subprocess.PIPE)
            raw = p.stdout.read().decode()
            status = [x.strip() for x in raw.split('\n')]
            print(status)
            if 'active' == status[2].split(' ')[1]:
                pass
            else:
                logging.error(raw)
                red.on()
            
