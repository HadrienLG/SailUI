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

# Configuration
import config.hardware as hardware

# Generic/Built-in
import datetime
import serial
import time
import os
import socket
import sys
import threading
from subprocess import check_call
import logging
import paho.mqtt.client as mqtt
import pynmea2

# Sensors
from libs.LEDplus import LEDplus
from gpiozero import Button, LED

# Project modules
from database import DataBase

# Owned
__author__ = "HadrienLG"
__copyright__ = "Copyright 2021, SailUI"
__credits__ = ["HadrienLG", "ChrisBiau",]
__license__ = "MIT"
__version__ = "0.2.0"
__maintainer__ = "HadrienLG"
__email__ = "hadrien.lg@wanadoo.fr"
__status__ = "OnGoing"
__influence__ = {'InfluxDB':'https://www.influxdata.com/blog/getting-started-python-influxdb/',
                 'Socket_Thread':'https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/',
                 'Server_Client':'https://stackoverflow.com/questions/43513337/multiclient-server-in-python-how-to-broadcast',
                 'NMEA parsing':'https://github.com/Knio/pynmea2',
                 'Waveshare Sense HAT': 'https://www.waveshare.com/wiki/Sense_HAT_(B)',
                 'MQTT': 'https://pypi.org/project/paho-mqtt/'}

# Logging
logging.basicConfig(filename='sailui_publish_gps.log', level=logging.DEBUG)
logging.info('Démarrage de SailUI-Publish GPS, début de journalisation')


def thread_serial(threadstop, db_pos, mqttclient, status_led):
    identifiants = ['GGA', 'GLL', 'GSV', 'GSA', 'VTG', 'RMC']
    
    while True:
        try:
            # Lecture d'une ligne et décodage
            ligne = serialPort.readline()
            phrase = ligne.decode("utf-8")
            logging.debug('[SERIAL] {}'.format(phrase))
            
            # Envoi à la base de données de la phrase NMEA brute
            db_pos.add_point(phrase)

            # Si la phrase NMEA nous intéresse, on la partage aux clients
            id_nmea = phrase[3:6]
            if id_nmea in identifiants:
                topic = f"gps/{id_nmea}"
                result = mqttclient.publish(topic,phrase) # result: [code, message_id]
                if result[0] != 0:
                    logging.exception(f"Echec de l'envoi du message NMEA {id_nmea} au broker")
                if id_nmea == 'RMC':
                    nmeaRMC = pynmea2.parse(phrase)
                    msgs = [{'topic':"gps/info/latitude", 'payload':nmeaRMC.latitude},
                            {'topic':"gps/info/longitude", 'payload':nmeaRMC.longitude},]
                    for msg in msgs:
                        result = mqttclient.publish(msg['topic'],msg['payload'])
                        if result[0] != 0:
                            logging.exception(f"Echec de l'envoi du message NMEA RMC au broker: {msg}")
                if id_nmea == 'VTG':
                    nmeaVTG = pynmea2.parse(phrase)
                    msgs = [{'topic':"gps/info/vitesse", 'payload':nmeaVTG.data[4]}, # 'Speed over ground knots'
                            {'topic':"gps/info/cap", 'payload':nmeaVTG.data[0]}, # 'True Track made good'
                            ]
                    for msg in msgs:
                        result = mqttclient.publish(msg['topic'],msg['payload'])
                        if result[0] != 0:
                            logging.exception(f"Echec de l'envoi du message NMEA VTG au broker: {msg}")
        # Gestion des erreurs
        except(UnicodeError):
            logging.exception('ThreadSerial, erreur Unicode: ',ligne)
        if not threadstop():
            logging.info('Arrêt du thread Serial')
            print('Arrêt du thread Serial',threadstop())
            break
            
def killsignal():
    logging.info('Lancement du kill signal')
    user_signal = False

def shutdown():
    logging.info('Extinction demandée')
    check_call(['sudo', 'poweroff'])
    
# [MQTT] The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info('Connected to MQTT broker successfully!')
    else:
        logging.warning("Connected with result code " + mqtt.connack_string(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# [MQTT] The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print(msg.topic+" "+str(msg.payload))
    pass

# [MQTT] The callback for when a PUBLISH message is send to the server.
def on_publish(mosq, obj, mid):
    #print("Publish mid: " + str(mid))
    pass


if __name__ == '__main__':
    logging.debug('Initialisation du programme')
    
    ##############################################
    # 0. Initialisation des différents composants
    ##############################################
    # - GPIOs
    # - port série
    # - mqtt client
    
    user_signal = True
     
    # Initialisation de la led jaune de status, allumage 1s puis extinction
    yellow1 = LEDplus(hardware.leds['yellow1'])
    yellow1.on()
    time.sleep(1)
    yellow1.off()
    logging.info(f'LED jaune1 démarrée')
    
    # Initialisation du port série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    logging.info(f'Série, port {port} connecté')

    # Connection à la base InfluxDB
    InfluxPosition = DataBase('position')
    logging.info(f'InfluxDB, connexions au serveur établie')
    
    # Client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.connect("127.0.0.1", 1883, 60)
    client.loop_start()
    logging.info(f'MQTT, connexions au serveur établie')
    
    ##############################################
    # 1. Lancement des threads
    ##############################################
    # - écoute du port série/GPS et envoi à la BDD
    
    stop_thread = lambda : user_signal
    
    # Ecoute du port série
    threadSerial_name = "Lecture du port série"
    threadSerial = threading.Thread( target=thread_serial,
                                     args=(stop_thread, InfluxPosition, client, yellow1) )
    threadSerial.setName( threadSerial_name )
    threadSerial.start()
    logging.info(f'Thread {threadSerial_name} démarré')
    yellow1.blink(0.5)
        
    ##############################################
    # 2. Supervision des threads
    ##############################################
    # - Boucle permanente pour superviser les threads
    
    while True and user_signal:
        time.sleep(1) # Toutes les secondes
        try:
            if not threadSerial.is_alive():
                message = '[{}] {} {}'.format(time.ctime(), threadSerial.getName(), threadSerial.is_alive())
                logging.warning(message)
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            user_signal = False
            InfluxPosition.close()
            yellow1.off()
            logging.info("Done.\nExiting.")
    else:
        print('Kill signal has been pressed...')
        killsignal()
        InfluxPosition.close()
        logging.info('Going to shut down now...')
        # shutdown()
