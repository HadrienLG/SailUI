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


# Generic/Built-in
import datetime
import serial
import time
import os
import sys
import threading
from subprocess import check_call
import logging
import paho.mqtt.client as mqtt

# Sensors
from libs.AD import ADS1015 # Amplificateur de gain
from libs.ICM20948 import ICM20948 # Giroscope
from libs.LPS22HB import LPS22HB # Pression, température
from libs.TCS34725 import TCS34725 # Couleurs
#from libs.SHTC3 import SHTC3 # Température, humidité
import busio
import board
import adafruit_shtc3


# Owned
__author__ = "HadrienLG"
__copyright__ = "Copyright 2021, SailUI"
__credits__ = ["HadrienLG", "ChrisBiau",]
__license__ = "MIT"
__version__ = "0.3.0"
__maintainer__ = "HadrienLG"
__email__ = "hadrien.lg@wanadoo.fr"
__status__ = "OnGoing"
__influence__ = {'Waveshare Sense HAT': 'https://www.waveshare.com/wiki/Sense_HAT_(B)'}

# Logging
logging.basicConfig(filename='sailui_publish_sensors.log', level=logging.DEBUG)
logging.info('Démarrage de SailUI-Publish sensors, début de journalisation')

user_signal = True # variable global de boucle infinie
axes = ['x','y','z']

def thread_gyro(threadstop, mqttclient, gyro):
    while True:
        # Gyroscope
        gyro.icm20948update()
        roll, pitch, yaw = icm20948.Roll, icm20948.Pitch, icm20948.Yaw
        acceleration = icm20948.Acceleration
        gyroscope = icm20948.Gyroscope
        magnetic = icm20948.Magnetic
        
        message = '[GYROSCOPE]\n' + \
                      'Roll = {:.2f}, Pitch = {:.2f}, Yaw = {:.2f}\n'.format(roll, pitch, yaw) + \
                      'Acceleration:  X = {}, Y = {}, Z = {}\n'.format(acceleration[0], acceleration[1], acceleration[2]) + \
                      'Gyroscope:     X = {}, Y = {}, Z = {}\n'.format(gyroscope[0], gyroscope[1], gyroscope[2]) + \
                      'Magnetic:      X = {}, Y = {}, Z = {}'.format(magnetic[0], magnetic[1], magnetic[2])
        logging.debug(message)

        # MQTT
        for ax in zip(['roll', 'pitch', 'yaw'], [roll, pitch, yaw]):
            result = mqttclient.publish(f'gyro/{ax[0]}',ax[1]) # result: [code, message_id]
            if result[0] != 0:
                logging.exception(f"Gyroscope, échec de l'envoi du message roll/pich/yaw au broker")
        for field in zip(['acceleration', 'gyroscope', 'magnetic'], [acceleration, gyroscope, magnetic]):
            for ax in range(0,3):
                result = mqttclient.publish(f'gyro/{field[0]}/{axes[ax]}',field[1][ax]) # result: [code, message_id]
                if result[0] != 0:
                    logging.exception(f"Gyroscope, échec de l'envoi du message au broker")
        
        if not threadstop():
            logging.info('Arrêt du thread Gyroscope')
            print('Arrêt du thread Gyroscope',threadstop())
            break
        
def thread_baro(threadstop, mqttclient, baro):
    while True:
        time.sleep(5)
        # Baromètre
        baro.update()
        pression, temperature = baro.PRESS_DATA, baro.TEMP_DATA
        logging.debug('[BAROMETRE] Pressure = {:6.2f} hPa , Temperature = {:6.2f} °C'.format(pression, temperature) )
        
        # MQTT
        result = mqttclient.publish(f'baro/pression',pression) # result: [code, message_id]
        if result[0] != 0:
            logging.exception(f"Barometre, échec de l'envoi du message pression au broker")
        
        result = mqttclient.publish(f'baro/temperature', temperature) # result: [code, message_id]
        if result[0] != 0:
            logging.exception(f"Barometre, échec de l'envoi du message temperature au broker")
        
        if not threadstop():
            logging.info('Arrêt du thread Barometre')
            print('Arrêt du thread Barometre',threadstop())
            break

def thread_therm(threadstop, mqttclient, therm):
    while True:
        time.sleep(1)
        # Thermomètre
        temperature, humidite = therm.measurements
        logging.debug('[THERMOMETRE] Temperature = {:6.2f}°C , Humidity = {:6.2f}%%'.format(temperature, humidite) )
        
        # MQTT
        result = mqttclient.publish(f'therm/temperature',temperature) # result: [code, message_id]
        if result[0] != 0:
            logging.exception(f"Thermometre, échec de l'envoi du message temperature au broker")
        
        result = mqttclient.publish(f'therm/humidite', humidite) # result: [code, message_id]
        if result[0] != 0:
            logging.exception(f"Thermometre, échec de l'envoi du message au broker")
        
        if not threadstop():
            logging.info('Arrêt du thread Thermometre')
            print('Arrêt du thread Thermometre',threadstop())
            break


# [MQTT] The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info('Connected to MQTT broker successfully!')
    else:
        logging.warning("Connected with result code "+mqtt.connack_string(rc))

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
    ##############################################
    # 0. Initialisation des différents composants
    ##############################################
    # - GPIOs
    # - base influxdb
    # - gyroscope
    # - Baromètre
    # - Thermomètre
    logging.debug('Initialisation du programme')
 
    # Initialisation des capteurs
    MotionVal = [0.0 for _ in range(0,9)]
    icm20948 = ICM20948() # Gyroscope
    lps22hb = LPS22HB() # Pression/température
    i2c = busio.I2C(board.SCL, board.SDA)
    shtc3 = adafruit_shtc3.SHTC3(i2c) # Température/humidité
    logging.info('Capteurs initialisés')
    
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
    # - écoute du baromètre
    # - écoute du thermomètre
    # - écoute du gyroscope
    
    stop_thread = lambda : user_signal
    
    # Ecoute des capteurs thread_capteurs(threadname, gyro, baro, therm):
    threads_capteurs = []
    for capteur in zip([icm20948, lps22hb, shtc3], ['Gyroscope', 'Baromètre', 'Thermomètre'], [thread_gyro, thread_baro, thread_therm]):
        threadObj = threading.Thread( target=capteur[2], args=(stop_thread, client, capteur[0]), name=capteur[1]  )
        threads_capteurs.append(threadObj)
        threadObj.start()
        logging.info(f'Thread {capteur[1]} démarré')
        
    ##############################################
    # 2. Supervision des threads
    ##############################################
    # - Boucle permanente pour superviser les threads
    
    while True and user_signal:
        time.sleep(1) # Toutes les secondes
        try:
            for thr in threads_capteurs:                
                if not thr.is_alive():
                    message = '[{}] {} {}'.format(time.ctime(), thr.getName(), thr.is_alive())
                    logging.warning(message)            
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            user_signal = False
            logging.info("Done.\nExiting.")
    else:
        logging.info('Going to shut down now...')