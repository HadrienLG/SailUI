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

# Other Libs
import pynmea2
from influxdb import InfluxDBClient,exceptions

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
                 'NMEA parsing':'https://github.com/Knio/pynmea2'}


# Préparation du client vers la base de données
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


if __name__ == '__main__':
    # Entrée série
    port = "/dev/serial0"
    serialPort = serial.Serial(port, baudrate = 9600, timeout = 0.5)

    # Connection à la base InfluxDB
    client = connectInfluxDBClient()

    # Boucle principale : lecture sur le port série, envoi vers InfluxDB
    boucle = True
    while boucle:
        try:
            # Lecture d'une ligne et décodage
            ligne = serialPort.readline()
            phrase = ligne.decode("utf-8")
            print(phrase)
            # Si la phrase NMEA nous intéresse, on l'exploite
            if 'RMC' in phrase:
                charge = rmc2payloads(phrase)
                if charge['fields']['latitude'] != 0 and charge['fields']['longitude'] != 0:
                    print(charge)
                    client.write_points([charge])
            if 'GLL' in phrase:
                charge = gll2payloads(phrase)
                if charge['fields']['latitude'] != 0 and charge['fields']['longitude'] != 0:
                    print(charge)
                    client.write_points([charge])
        
        # Gestion des erreurs
        except(UnicodeError):
            print('Erreur : ',ligne)
        except(TypeError, pynmea2.ParseError):
            print('Erreur : ',ligne)
        except(exceptions.InfluxDBClientError):
            client = connectInfluxDBClient()
        except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
            print("Done.\nExiting.")
            boucle = False
            client.close()
 