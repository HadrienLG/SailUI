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
import socket
import sys
import threading
from subprocess import check_call
import logging

# Sensors
from libs.LEDplus import LEDplus
from libs.AD import ADS1015 # Amplificateur de gain
from libs.ICM20948 import ICM20948 # Giroscope
from libs.LPS22HB import LPS22HB # Pression, température
from libs.TCS34725 import TCS34725 # Couleurs
#from libs.SHTC3 import SHTC3 # Température, humidité
import busio
import board
import adafruit_shtc3
from gpiozero import Button, LED

# Project modules
from server_sockets import Server, Client
from database import DataBase

# Owned
__author__ = "HadrienLG"
__copyright__ = "Copyright 2021, SailUI"
__credits__ = ["HadrienLG", "ChrisBiau",]
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "HadrienLG"
__email__ = "hadrien.lg@wanadoo.fr"
__status__ = "OnGoing"
__influence__ = {'InfluxDB':'https://www.influxdata.com/blog/getting-started-python-influxdb/',
                 'Socket_Thread':'https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/',
                 'Server_Client':'https://stackoverflow.com/questions/43513337/multiclient-server-in-python-how-to-broadcast',
                 'NMEA parsing':'https://github.com/Knio/pynmea2',
                 'Waveshare Sense HAT': 'https://www.waveshare.com/wiki/Sense_HAT_(B)'}

# Logging
logging.basicConfig(filename='sailui_server.log', level=logging.DEBUG)
logging.info('Démarrage de SailUI-Server, début de journalisation')

debug = False
user_signal = True # variable global de boucle infinie

def thread_new_clients(threadstop, sss, status_led):
    while True:
        sss.wait_clients(status_led) # démarre le socket et attend les connections des clients
        if not threadstop():
            print('Arrêt du thread New Client',threadstop())
            break

def thread_listen_clients(threadstop, sss, db_evt):
    while True:
        sss.recv_clients(db_evt) # écoute tous les messages venant des clients
        if not threadstop():
            logging.info('Arrêt du thread Listen Client')
            print('Arrêt du thread Listen Client',threadstop())
            break

def thread_gyro(threadstop, db_cap, gyro):
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
        db_cap.add_info( {'type':'gyroscope', 'roll':roll, 'pitch':pitch, 'yaw':yaw,
                          'acceleration':acceleration, 'gyroscope':gyroscope, 'magnetic':magnetic} )
        if not threadstop():
            logging.info('Arrêt du thread Gyroscope')
            print('Arrêt du thread Gyroscope',threadstop())
            break
        
def thread_baro(threadstop, db_cap, baro):
    while True:
        time.sleep(5)
        # Baromètre
        baro.update()
        pression, temperature = baro.PRESS_DATA, baro.TEMP_DATA
        logging.debug('[BAROMETRE] Pressure = {:6.2f} hPa , Temperature = {:6.2f} °C'.format(pression, temperature) )
        db_cap.add_info( {'type':'barometre', 'pression':pression, 'temperature':temperature} )
        if not threadstop():
            logging.info('Arrêt du thread Barometre')
            print('Arrêt du thread Barometre',threadstop())
            break

def thread_therm(threadstop, db_cap, therm):
    while True:
        time.sleep(1)
        # Thermomètre
        temperature, humidite = therm.measurements
        logging.debug('[THERMOMETRE] Temperature = {:6.2f}°C , Humidity = {:6.2f}%%'.format(temperature, humidite) )
        db_cap.add_info( {'type':'thermometre', 'temperature':temperature, 'humidite':humidite} )
        if not threadstop():
            logging.info('Arrêt du thread Thermometre')
            print('Arrêt du thread Thermometre',threadstop())
            break

def thread_serial(threadstop, db_pos, sss, status_led):
    while True:
        try:
            # Lecture d'une ligne et décodage
            ligne = serialPort.readline()
            phrase = ligne.decode("utf-8")
            logging.debug('[SERIAL] {}'.format(phrase))
            
            # Envoi à la base de données de la phrase NMEA brute
            db_pos.add_point(phrase)

            # Si la phrase NMEA nous intéresse, on la partage aux clients
            if 'RMC' in phrase:
                try:
                    cast_msg = str.encode(phrase)
                    sss.send_to_all_clients(cast_msg)
                except:
                    logging.exception('Echec de l''envoi du message NMEA RMC à tous les clients')
                    
        # Gestion des erreurs
        except(UnicodeError):
            logging.exception('Erreur : ',ligne)
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


if __name__ == '__main__':  
    ##############################################
    # 0. Initialisation des différents composants
    ##############################################
    # - GPIOs
    # - port série
    # - base influxdb
    # - socket/server
    # - gyroscope
    # - Baromètre
    # - Thermomètre
    logging.debug('Initialisation du programme')
        
    # Initialisation des GPIO
    powerLED = LEDplus(16)
    powerLED.on()
    
    green = LEDplus(22)    
    red = LEDplus(17)    
    yellow1 = LEDplus(23)
    yellow2 = LEDplus(24)
    leds = [green, red, yellow1, yellow2]
    
    for led in leds:
        led.on()
    time.sleep(1)
    for led in leds:
        led.off()
    
    powerB = Button(19, hold_time=5) # Si appui 5sec
    powerB.when_held = killsignal # Alors déclenchement du signal d'arrêt
    
    green.blink(1) # Clignottement durant l'initialisation
    
    # Initialisation du port série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    logging.info(f'Port {port} connecté')

    # Connection à la base InfluxDB
    InfluxPosition = DataBase('position')
    InfluxCapteurs = DataBase('capteurs')
    InfluxEvenment = DataBase('evenements')
    logging.info(f'Connexions au serveur InfluxDB établie')
    
    # Socket serveur pour diffuser les trames aux clients
    ServerSideSocket = Server('0.0.0.0', 10111)
    logging.info("Socket ouvert à l'adresse 127.0.0.1:10111")
    
    # Initialisation des capteurs
    MotionVal = [0.0 for _ in range(0,9)]
    icm20948 = ICM20948() # Gyroscope
    lps22hb = LPS22HB() # Pression/température
    i2c = busio.I2C(board.SCL, board.SDA)
    shtc3 = adafruit_shtc3.SHTC3(i2c) # Température/humidité
    logging.info('Capteurs initialisés')
    
    ##############################################
    # 1. Lancement des threads
    ##############################################
    # - écoute du port série/GPS et envoi aux clients et BDD
    # - écoute du baromètre
    # - écoute du thermomètre
    # - écoute du gyroscope
    # - attente des clients/socket
    # - gestion des messages clients
    
    stop_thread = lambda : user_signal
    
    # Ecoute du port série
    threadSerial_name = "Lecture du port série"
    threadSerial = threading.Thread( target=thread_serial,
                                     args=(stop_thread, InfluxPosition, ServerSideSocket, yellow1) )
    threadSerial.setName( threadSerial_name )
    threadSerial.start()
    logging.info(f'Thread {threadSerial_name} démarré')
    yellow1.blink(0.5)
    
    # Ecoute des capteurs thread_capteurs(threadname, gyro, baro, therm):
    threads_capteurs = []
    for capteur in zip([icm20948, lps22hb, shtc3], ['Gyroscope', 'Baromètre', 'Thermomètre'], [thread_gyro, thread_baro, thread_therm]):
        threadObj = threading.Thread( target=capteur[2], args=(stop_thread, InfluxCapteurs, capteur[0]) )
        threadObj.setName( capteur[1] )
        threads_capteurs.append(threadObj)
        threadObj.start()
        logging.info(f'Thread {capteur[1]} démarré')    
    
    # Gestion des nouveaux clients
    threadNClient_name = "Gestion des nouveaux clients"
    threadNClient = threading.Thread( target=thread_new_clients,
                                      args=(stop_thread, ServerSideSocket, yellow2) )
    threadNClient.setName( threadNClient_name )
    threadNClient.start()
    logging.info(f'Thread {threadNClient_name} démarré')
    yellow2.blink(0.5)
    
    # Ecoute des clients connectés
    threadLClient_name = "Ecoute des clients"
    threadLClient = threading.Thread( target=thread_listen_clients,
                                      args=(stop_thread, ServerSideSocket, InfluxEvenment) )
    threadLClient.setName( threadLClient_name )
    threadLClient.start()
    logging.info(f'Thread {threadLClient_name} démarré')
    
    threads = [threadSerial, threadNClient, threadLClient] + threads_capteurs
    
    ##############################################
    # 2. Supervision des threads
    ##############################################
    # - Boucle permanente pour superviser les threads
    
    green.on() # ça tourne
    while True and user_signal:
        time.sleep(1) # Toutes les secondes
        try:
            for thr in threads:                
                if not thr.is_alive():
                    red.on()
                    message = '[{}] {} {}'.format(time.ctime(), thr.getName(), thr.is_alive())
                    logging.warning(message)            
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            user_signal = False
            ServerSideSocket.close()
            ClientInflux.close()
            logging.info("Done.\nExiting.")
            for led in leds:
                led.off()
    else:
        print('Kill signal has been pressed...')
        powerLED.blink(0.2)
        ServerSideSocket.close()
        killsignal()
        InfluxPosition.close()
        InfluxCapteurs.close()
        InfluxEvenment.close()
        for led in leds:
            led.off()
        time.sleep(1)
        logging.info('Going to shut down now...')
        powerLED.off()
        # shutdown()
