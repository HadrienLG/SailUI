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

# Project modules
from utils import rmc2payloads, gll2payloads

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
                 'NMEA parsing':'https://github.com/Knio/pynmea2'}


# classe des clients connectés au serveur dans des Thread séparés
class Client(threading.Thread):
    def __init__(self, ip, port, connection):
        threading.Thread.__init__(self)
        self.connection = connection
        self.ip = ip
        self.port = port
        
    def __str__(self):
        return f'Client {self.ip}:{self.port}'
        
    def __repr__(self):
        return {ip:self.ip, port:self.port}

    def run(self):
        while True:
            data = self.connection.recv(1024)
            if data :
                self.connection.sendall(data)
            else :
                break
        self.connection.close()

# classe du serveur qui gère sa liste de client
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.address = (self.ip, self.port)
        self.server = None
        self.clients = []

    def send_to_all_clients(self, msg):
        for client in self.clients :
            try:
                client.connection.send(msg)
            except:
                self.clients.remove(client)
                print(f'Client {client} déconnecté')

    def send_to_client(self, ip, port, msg):
        for client in self.clients :
            if client.ip == ip and client.port == port :
                try:
                    client.connection.send(msg)
                except:
                    self.clients.remove(client)
                    print(f'Client {client} déconnecté')

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(self.address)
        except socket.error as e:
            if self.server:
                self.server.close()
            sys.exit(1)

    def wait_clients(self):
        #TODO : à threader en parallèle de l'écoute des messages clients
        self.open_socket()
        self.server.listen(10)

        while True :
            # Gestion des nouveaux clients
            connection, (ip, port) = self.server.accept()
            c = Client(ip, port, connection)
            c.start()
            self.clients.append(c)
            
            # Supervision des clients connectés
            print('[{}] Client(s) connecté(s) : {}'.format(time.ctime(),len(self.clients)))
            for client in self.clients:
                print(client)

        self.server.close()
    
    def recv_clients(self):
        #TODO : à threader en parallèle des connections des nouveaux clients
        # Surveillance des clients connectés
        # for client in self.clients:
        #     try:
        #         message = client.connection.recv(1024).decode()
        #         print(f'Client {client} dit : {message}')
        #     except:
        #         print(f'Client {client} muet')
            


# Gestion de la connexion vers la base InfluxDB
def connectInfluxDBClient():
    client = InfluxDBClient(host='localhost', port=8086)
    all_influxDB = client.get_list_database()
    if 'position' in [list(x.values())[0] for x in client.get_list_database()]:
         print('Base de données position disponible')
    else:
        client.create_database('position')
        print('Base de données position créée')
    client.switch_database('position')
    return client



def thread_clients(threadname, sss):
    sss.wait_clients() # démarre le socket et attend les connections des clients


def thread_serial(threadname, cidb, sss):
    while True:
        try:
            # Lecture d'une ligne et décodage
            ligne = serialPort.readline()
            phrase = ligne.decode("utf-8")
            # print(phrase)
            # Si la phrase NMEA nous intéresse, on l'exploite
            if 'RMC' in phrase:
                charge = rmc2payloads(phrase)
                if charge['fields']['latitude'] != 0 and charge['fields']['longitude'] != 0:
                    print(charge)
                    cidb.write_points([charge])
                    cast_msg = str.encode(phrase)
                    print(cast_msg)
                    sss.send_to_all_clients(cast_msg)
            if 'GLL' in phrase:
                charge = gll2payloads(phrase)
                if charge['fields']['latitude'] != 0 and charge['fields']['longitude'] != 0:
                    # print(charge)
                    cidb.write_points([charge])
        
        # Gestion des erreurs
        except(UnicodeError):
            print('Erreur : ',ligne)
        except(TypeError, pynmea2.ParseError):
            print('Erreur : ',ligne)
        except(exceptions.InfluxDBClientError):
            cidb = connectInfluxDBClient()


if __name__ == '__main__':
    user_signal = True
    
    # Initialisation du port série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    print(f'Port {port} connecté')

    # Connection à la base InfluxDB
    ClientInflux = connectInfluxDBClient()
    print(f'Connexion au serveur InfluxDB établie')
    
    # Socket serveur pour diffuser les trames aux clients
    ServerSideSocket = Server('127.0.0.1', 10111)
    
    # Multithread de la gestion client et de l'entrée série
    threadSerial_name = "Thread lecture du port série"
    threadSerial = threading.Thread( target=thread_serial, args=("Thread lecture du port série", ClientInflux, ServerSideSocket) )
    threadSerial.setName( threadSerial_name )
    threadSerial.start()
    print(f'{threadSerial_name} démarré')
    
    threadClient_name = "Thread gestion des clients"
    threadClient = threading.Thread( target=thread_clients, args=(threadClient_name, ServerSideSocket) )
    threadClient.setName( threadClient_name )
    threadClient.start()
    print(f'{threadClient_name} démarré')
    
    while True and user_signal:
        time.sleep(1)
        try:
            print('[',time.ctime(),']')
            print(threadClient.getName(), threadClient.is_alive())
            print(threadSerial.getName(), threadSerial.is_alive())
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            user_signal = False
            ServerSideSocket.close()
            ClientInflux.close()
            print("Done.\nExiting.")
    
    # TODO : gérer la fin (cloture des connexions)
    threadClient.join()
    threadSerial.join()
    ServerSideSocket.close()
    ClientInflux.close()
    
