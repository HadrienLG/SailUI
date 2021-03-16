# encoding: utf8
"""
SailUI - GPS data from serial port parsed and send to InfluxDB

MIT License

Copyright (c) 2020 HadrienLG

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
from queue import Queue
import time
import os
import socket
import sys
import threading

# Other Libs
import pynmea2
from influxdb import InfluxDBClient,exceptions

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

# Project modules
from server_sockets import Server, Client
from database import DataBase

# Owned
__author__ = "HadrienLG"
__copyright__ = "Copyright 2020, SailUI"
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


def thread_new_clients(threadname, sss, status_led):
    sss.wait_clients(status_led) # démarre le socket et attend les connections des clients

def thread_listen_clients(threadname, sss):
    sss.recv_clients() # écoute tous les messages venant des clients

def thread_capteurs(threadname, gyro, baro, therm):
    PRESS_DATA = 0.0
    TEMP_DATA = 0.0
    u8Buf = [0,0,0]
    
    while True:
        # Gyroscope
        gyro.icm20948update()
        print("-------------------------------------------------------------")
        print('Roll = {:.2f}, Pitch = {:.2f}, Yaw = {:.2f}'.format(icm20948.Roll, icm20948.Pitch, icm20948.Yaw))
        print('Acceleration:  X = {}, Y = {}, Z = {}'.format(icm20948.Acceleration[0], icm20948.Acceleration[1], icm20948.Acceleration[2]))  
        print('Gyroscope:     X = {}, Y = {}, Z = {}'.format(icm20948.Gyroscope[0], icm20948.Gyroscope[1], icm20948.Gyroscope[2]))
        print('Magnetic:      X = {}, Y = {}, Z = {}'.format(icm20948.Magnetic[0], icm20948.Magnetic[1], icm20948.Magnetic[2]))
        
        # Baromètre
        baro.LPS22HB_START_ONESHOT()
        if (baro._read_byte(LPS_STATUS)&0x01)==0x01:  # a new pressure data is generated
            u8Buf[0]=baro._read_byte(LPS_PRESS_OUT_XL)
            u8Buf[1]=baro._read_byte(LPS_PRESS_OUT_L)
            u8Buf[2]=baro._read_byte(LPS_PRESS_OUT_H)
            PRESS_DATA=((u8Buf[2]<<16)+(u8Buf[1]<<8)+u8Buf[0])/4096.0
        if (baro._read_byte(LPS_STATUS)&0x02)==0x02:   # a new pressure data is generated
            u8Buf[0]=baro._read_byte(LPS_TEMP_OUT_L)
            u8Buf[1]=baro._read_byte(LPS_TEMP_OUT_H)
            TEMP_DATA=((u8Buf[1]<<8)+u8Buf[0])/100.0
        print("-------------------------------------------------------------")
        print('Pressure = %6.2f hPa , Temperature = %6.2f °C\r\n'%(PRESS_DATA,TEMP_DATA))

        # Thermomètre
        temperature, humidite = therm.measurements
        print("-------------------------------------------------------------")
        print('Temperature = {%6.2}f°C , Humidity = {%6.2}f%%'.format(temperature, humidite))

def thread_serial(threadname, cidb, sss, status_led):
    while True:
        try:
            # Lecture d'une ligne et décodage
            ligne = serialPort.readline()
            phrase = ligne.decode("utf-8")
            print(phrase)
            
            # Envoi à la base de données de la phrase NMEA brute
            cidb.add_point(phrase)

            # Si la phrase NMEA nous intéresse, on l'exploite
            if 'RMC' in phrase:
                cast_msg = str.encode(phrase)
                sss.send_to_all_clients(cast_msg)
        
        # Gestion des erreurs
        except(UnicodeError):
            print('Erreur : ',ligne)


if __name__ == '__main__':
    user_signal = True
    
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
    
    # Initialisation des GPIO
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
    
    green.blink(1) # Clignottement durant l'initialisation
    
    # Initialisation du port série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    print(f'Port {port} connecté')

    # Connection à la base InfluxDB
    ClientInflux = DataBase('position')
    print(f'Connexion au serveur InfluxDB établie')
    
    # Socket serveur pour diffuser les trames aux clients
    ServerSideSocket = Server('127.0.0.1', 10111)
    print("Socket ouvert à l'adresse 127.0.0.1:10111")
    
    # Initialisation des capteurs
    MotionVal = [0.0 for _ in range(0,9)]
    icm20948 = ICM20948() # Gyroscope
    lps22hb = LPS22HB() # Pression/température
    i2c = busio.I2C(board.SCL, board.SDA)
    shtc3 = adafruit_shtc3.SHTC3(i2c) # Température/humidité
    
    ##############################################
    # 1. Lancement des threads
    ##############################################
    # - écoute du port série/GPS et envoi aux clients et BDD
    # - écoute du baromètre
    # - écoute du thermomètre
    # - écoute du gyroscope
    # - attente des clients/socket
    # - gestion des messages clients
    
    # Ecoute du port série
    threadSerial_name = "Thread lecture du port série"
    threadSerial = threading.Thread( target=thread_serial,
                                     args=("Thread lecture du port série",
                                           ClientInflux,
                                           ServerSideSocket,
                                           yellow1) )
    threadSerial.setName( threadSerial_name )
    threadSerial.start()
    print(f'{threadSerial_name} démarré')
    yellow1.blink(0.5)
    
    # Ecoute des capteurs thread_capteurs(threadname, gyro, baro, therm):
    threadCapteurs_name = "Thread capteurs"
    threadCapteurs = threading.Thread( target=thread_capteurs,
                                     args=(threadCapteurs_name,
                                           icm20948,
                                           lps22hb,
                                           shtc3) )
    threadCapteurs.setName( threadCapteurs_name )
    threadCapteurs.start()
    print(f'{threadCapteurs_name} démarré')
    
    # Gestion des nouveaux clients
    threadNClient_name = "Thread gestion des clients"
    threadNClient = threading.Thread( target=thread_new_clients,
                                      args=(threadNClient_name,
                                            ServerSideSocket,
                                            yellow2) )
    threadNClient.setName( threadNClient_name )
    threadNClient.start()
    print(f'{threadNClient_name} démarré')
    yellow2.blink(0.5)
    
    # Ecoute des clients connectés
    threadLClient_name = "Thread gestion des clients"
    threadLClient = threading.Thread( target=thread_listen_clients,
                                      args=(threadLClient_name,
                                            ServerSideSocket) )
    threadLClient.setName( threadLClient_name )
    threadLClient.start()
    print(f'{threadLClient_name} démarré')
    
    threads = [threadSerial, threadCapteurs,
               threadNClient, threadLClient]
    
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
                    print('[',time.ctime(),']', thr.getName(), thr.is_alive())            
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            user_signal = False
            ServerSideSocket.close()
            ClientInflux.close()
            print("Done.\nExiting.")
            for led in leds:
                led.off()
    
    # TODO : gérer la fin (cloture des connexions)
    threadClient.join()
    threadSerial.join()
    ServerSideSocket.close()
    ClientInflux.close()
    
