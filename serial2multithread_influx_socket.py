# Generic/Built-in
import datetime
import serial
from threading import Thread
from _thread import *
from queue import Queue
import time
import socket
import os

# Other Libs
import pynmea2
from influxdb import InfluxDBClient,exceptions

ThreadCount = 0

def rmc2payloads(phrase):
    message = pynmea2.parse(phrase)
    msg = dict(zip([x[0] for x in message.fields], message.data))
    charge = {"measurement":"RMC",
              "tags":{"talker": message.talker,
                      "status":msg['Status'],
                      "verbe":"RMC"
                      },
              "time":message.datetime.isoformat(),
              "fields":{
                      "latitude":message.latitude,
                      "longitude":message.longitude,
                      "vitesse":float(msg['Speed Over Ground']) if len(msg['Speed Over Ground'])>0 else float(0),
                      "heading":float(msg['True Course']) if len(msg['True Course'])>0 else float(0)
                      }
              }
    return charge

def gll2payloads(phrase):
    message = pynmea2.parse(phrase)
    msg = dict(zip([x[0] for x in message.fields], message.data))
    try:
        moment = datetime.datetime.strptime(msg['Timestamp'],'%H%M%S.%f').isoformat()
    except:
        moment = 0
    charge = {"measurement":"GLL",
              "tags":{"talker": message.talker,
                      "status":msg['Status'],
                      "verbe":"GLL"
                      },
              "time":moment,
              "fields":{
                      "latitude":message.latitude,
                      "longitude":message.longitude,
                      "Status":msg['Status'],
                      "FAA mode":msg['FAA mode indicator']
                      }
              }
    return charge


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


def multi_threaded_client(connection, q):
    connection.send(str.encode('Server is happy to connect with you!'))
    while True and kill_signal:
        phrase = q.get()
        if phrase:
            connection.sendall(str.encode(phrase))
        # data = connection.recv(2048)
        # response = 'Server message: ' + data.decode('utf-8')
        # if not data:
        #     break
        # connection.sendall(str.encode(response))
    connection.close()


def thread_clients(threadname, q, sss):
    global ThreadCount
    while True and kill_signal:
        # Gestion des connexions clients
        Client, address = sss.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        start_new_thread(multi_threaded_client, (Client, q))
        ThreadCount += 1
        print(f'Nombre de Thread clients : {ThreadCount}')

def thread_serial(threadname, q, cidb):
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
                    q.put(phrase)
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

    
if __name__ == "__main__":
    # Initialisation du port série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)

    # Connection à la base InfluxDB
    ClientInflux = connectInfluxDBClient()
    
    # Initialisation d'une file d'attente
    queue = Queue()
    
    # Création d'un socket côté serveur
    ServerSideSocket = socket.socket()
    host = '127.0.0.1'
    port = 10111
    try:
        ServerSideSocket.bind((host, port))
    except socket.error as e:
        print(str(e))

    print(f'Socket is listening on {host}:{port}...')
    ServerSideSocket.listen(5)
    
    # Création des threads et lancement
    kill_signal = True
    
    threadSerial_name = "Thread lecture du port série"
    threadSerial = Thread( target=thread_serial, args=("Thread lecture du port série", queue, ClientInflux) )
    threadSerial.setName( threadSerial_name )
    threadSerial.start()
    print(f'{threadSerial_name} démarré')
    
    threadClient_name = "Thread gestion des clients"
    threadClient = Thread( target=thread_clients, args=(threadClient_name, queue, ServerSideSocket) )
    threadClient.setName( threadClient_name )
    threadClient.start()
    print(f'{threadClient_name} démarré')

    # Boucle de surveillance de la vie des Threads
    while True and kill_signal:
        time.sleep(1)
        try:
            print('[',time.ctime(),']')
            print(threadClient.getName(), threadClient.is_alive())
            print(threadSerial.getName(), threadSerial.is_alive())
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            kill_signal = False
            ServerSideSocket.close()
            ClientInflux.close()
            print("Done.\nExiting.")
    
    # TODO : gérer la fin (cloture des connexions)
    threadClient.join()
    threadSerial.join()
    ServerSideSocket.close()
    ClientInflux.close()
