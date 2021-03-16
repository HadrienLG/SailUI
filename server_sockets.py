#!/usr/bin/python
# -*- coding:utf-8 -*-

# 'Socket_Thread':'https://www.positronx.io/create-socket-server-with-multiple-clients-in-python/',
# 'Server_Client':'https://stackoverflow.com/questions/43513337/multiclient-server-in-python-how-to-broadcast',

import threading
import socket
import time
import sys

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
                print(f'{client} déconnecté')

    def send_to_client(self, ip, port, msg):
        for client in self.clients :
            if client.ip == ip and client.port == port :
                try:
                    client.connection.send(msg)
                except:
                    self.clients.remove(client)
                    print(f'{client} déconnecté')

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(self.address)
        except socket.error as e:
            if self.server:
                self.server.close()
            sys.exit(1)
        except OSError:
            print('Merci de redémarrer les clients')

    def wait_clients(self, status_led=None):
        #TODO : à threader en parallèle de l'écoute des messages clients
        self.open_socket()
        self.server.listen(10)

        while True :
            # Gestion des nouveaux clients
            connection, (ip, port) = self.server.accept()
            c = Client(ip, port, connection)
            c.start()
            self.clients.append(c)
            num_clients = len(self.clients)
            
            # Supervision des clients connectés
            print('[{}] Client(s) connecté(s) : {}'.format(time.ctime(),num_clients))
            for client in self.clients:
                print(client)
                
            # Signalisation sur la led de status
            if num_clients > 0 and status_led is not None:
                status_led.train(num_clients)
    
    def recv_clients(self):
        while True:
            # Surveillance des clients connectés
            for client in self.clients:
                try:
                    message = client.connection.recv(1024).decode()
                    print(f'{client} dit : {message}')
                except:
                    print(f'{client} injoignable')
                    self.clients.remove(client)
                    print(f'{client} déconnecté')
            
