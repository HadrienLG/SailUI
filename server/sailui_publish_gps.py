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
import config.mqttbroker as mqttbroker

# Generic/Built-in
import datetime
import serial
import time
import os
import sys
import threading
from subprocess import check_call
import logging
import pynmea2

# Custom


# Owned
__author__ = "HadrienLG"
__copyright__ = "Copyright 2021, SailUI"
__credits__ = ["HadrienLG", "ChrisBiau",]
__license__ = "MIT"
__version__ = "0.3.0"
__maintainer__ = "HadrienLG"
__email__ = "hadrien.lg@wanadoo.fr"
__status__ = "OnGoing"
__influence__ = {'NMEA parsing':'https://github.com/Knio/pynmea2',
                 'Waveshare Sense HAT': 'https://www.waveshare.com/wiki/Sense_HAT_(B)',
                 'MQTT': 'https://pypi.org/project/paho-mqtt/'}

# Logging
logging.basicConfig(filename='sailui_publish_gps.log', level=logging.DEBUG)
logging.info('Démarrage de SailUI-Publish GPS, début de journalisation')

import paho.mqtt.client as mqtt

class MQTT():
    def __init__(self, adresse='127.0.0.1', port=1883, debug=False):
        # Création du client
        self.client = mqtt.Client()
        self.debug = debug
        
        # Définition des actions par défaut
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        
        # Connexion
        self.client.connect(adresse, port, 60)
        self.client.loop_start()
    
    # [MQTT] The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print('Connected to MQTT broker successfully!')
        else:
            print("Connected with result code " + mqtt.connack_string(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("$SYS/#")

    # [MQTT] The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        if self.debug:
            print(msg.topic+" : "+str(msg.payload.decode()))
        pass

    # [MQTT] The callback for when a PUBLISH message is send to the server.
    def on_publish(self, mosq, obj, mid):
        if self.debug:
            print("Publish mid: " + str(mid))
        pass
    
    # [MQTT] Publish
    def publish(self, sujet, message):
        return self.client.publish(sujet, message)

def nmea2payload(nmea):
    '''
    Mise en forme de la phrase NMEA vers une payload
    '''
    identifier = nmea.identifier()[2:]
    
    # Cas général
    msgs = []
    for champ, valeur in dict(zip(nmea.fields,nmea.data)).items():
            msgs.append({'topic':'gps/'+identifier+'/'+champ[1].strip().replace(' ','_'),
                         'payload':valeur})
    
    # Cas particulier
    if identifier == 'RMC':
        msgs.append({'topic':"gps/info/latitude", 'payload':nmea.latitude})
        msgs.append({'topic':"gps/info/longitude", 'payload':nmea.longitude})
        msgs.append({'topic':"gps/info/cap_vrai", 'payload':nmea.data[7]})
    
    if identifier == 'VTG':
        msgs.append({'topic':"gps/info/vitesse", 'payload':nmea.data[4]}) # 'Speed over ground knots'
        msgs.append({'topic':"gps/info/cap", 'payload':nmea.data[0]}) # 'True Track made good'

    if identifier == 'GGA':
        msgs.append({'topic':"gps/info/date", 'payload':nmea.data[0]}) # 'TimeStamp'
        msgs.append({'topic':"gps/info/sats", 'payload':nmea.data[6]}) # 'Number of Satellites in use'
        msgs.append({'topic':"gps/info/altitude", 'payload':nmea.data[8]})# 'Antenna Alt above sea level (mean)'

    if identifier == 'GLL':
        pass
    if identifier == 'GSA':
        pass
    if identifier == 'GSV':
        pass
    
    return msgs # payload


def thread_serial(var, serialPort, mqttclient):
    """
    Gestion des sorties du module ublox Max-M8Q
    Export vers le broker MQTT
    """
    identifiants = ['GGA', 'GLL', 'GSA', 'GSV', 'VTG', 'RMC']
    while True:
        try:
            # Lecture d'une ligne et décodage
            ligne = serialPort.readline()
            phrase = ligne.decode("utf-8")
            logging.debug(f'[UBLOX-M8Q] {phrase}')
            
            # Si la phrase NMEA nous intéresse, on la partage aux clients
            id_nmea = phrase[3:6]
            if id_nmea in identifiants:
                # Envoi du brut vers le broker MQTT
                result = mqttclient.publish(f"gps/{id_nmea}/raw",phrase) # result: [code, message_id]
                if result[0] != 0:
                    logging.exception(f"Echec de l'envoi du message NMEA {id_nmea} au broker")
                    
                # Extrait des phrases NMEA
                nmea = pynmea2.parse(phrase)
                
                # Envoi des détails au broker MQTT
                msgs = nmea2payload(nmea) # Préparation de la payload
                for msg in msgs:
                    result = mqttclient.publish(msg['topic'],msg['payload'])
                    if result[0] != 0:
                        logging.exception(f"Echec de l'envoi du message NMEA {id_nmea} au broker: {msg}")
        
        # Gestion des erreurs
        except(UnicodeError):
            logging.exception('ThreadSerial, erreur Unicode: ',ligne)

if __name__ == '__main__':
    logging.debug('Initialisation du programme')
    
    ##############################################
    # 0. Initialisation des différents composants
    ##############################################
   
    # Initialisation du port série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    logging.info(f'Série, port {port} connecté')
    
    # Client MQTT
    client = MQTT() # adresse=mqttbroker['adresse'], port=mqttbroker['port'])
    client.publish({'topic':"gps/server_status/datetime", 'payload':datetime.datetime.now().strftime('%H:%M:%S-%d/%m/%y')})
    client.publish({'topic':"gps/server_status/state", 'payload':'up'})
    logging.info(f'MQTT, connexions au serveur établie')
    
    ##############################################
    # 1. Lancement des threads
    ##############################################
    
    # Ecoute du port série
    threadSerial = threading.Thread( target=thread_serial, args=(0, serialPort, client), name="Lecture du port série" )
    threadSerial.start()
    logging.info(f'Thread {threadSerial.getName()} démarré')
        
    ##############################################
    # 2. Supervision des threads
    ##############################################    
    while True:
        time.sleep(1) # Toutes les secondes
        try:
            if not threadSerial.is_alive():
                message = '[{}] {} {}'.format(time.ctime(), threadSerial.getName(), threadSerial.is_alive())
                client.publish({'topic':"gps/server_status/datetime", 'payload':datetime.datetime.now().strftime('%H:%M:%S-%d/%m/%y')})
                client.publish({'topic':"gps/server_status/state", 'payload':'down'})
                logging.warning(message)
        except:
            logging.exception('ThreadSerial is down...')
    else:
        logging.info('Going to shut down now...')
