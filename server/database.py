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
import logging

# Other Libs
import pynmea2
from influxdb import InfluxDBClient,exceptions


class DataBase():
    def __init__(self, base_name='position'):
        self.client = InfluxDBClient(host='localhost', port=8086)
        all_influxDB = self.client.get_list_database()
        if base_name in [list(x.values())[0] for x in self.client.get_list_database()]:
             logging.info('Base de données {} disponible'.format(base_name))
        else:
            self.client.create_database(base_name)
            logging.info('Base de données {} créée'.format(base_name))
        self.client.switch_database(base_name)

    def add_point(self, nmea_phrase):
        try:
            message = pynmea2.parse(nmea_phrase)
            msg = dict(zip([x[0] for x in message.fields], message.data))
            if 'RMC' in message.identifier() and (message.latitude != 0 and message.longitude != 0):
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
            elif "GLL" in message.identifier() and (message.latitude != 0 and message.longitude != 0):
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
            
            if charge:
                self.client.write_points([charge])
        except pynmea2.ParseError:
            pass
        except UnboundLocalError:
            pass

    def add_info(self, charge):
        try:
            moment = datetime.datetime.strptime(msg['Timestamp'],'%H%M%S.%f').isoformat()
        except:
            moment = 0        
        mode = charge['type']
        if 'gyroscope' in mode:
            charge = {"measurement":"gyroscope",
                      "tags":{"sensor": 'ICM20948'},
                      "time":moment,
                      "fields":{
                              "roll":charge['roll'],
                              "pitch":charge['pitch'],
                              "yaw":charge['yaw'],
                              "acceleration_x":charge['acceleration'][0],
                              "acceleration_y":charge['acceleration'][1],
                              "acceleration_z":charge['acceleration'][2],
                              "gyroscope_x":charge['gyroscope'][0],
                              "gyroscope_y":charge['gyroscope'][1],
                              "gyroscope_z":charge['gyroscope'][2],
                              "magnetic_x":charge['magnetic'][0],
                              "magnetic_y":charge['magnetic'][1],
                              "magnetic_z":charge['magnetic'][2]
                              }
                          }
        elif 'barometre' in mode:
            charge = {"measurement":"barometre",
                      "tags":{"sensor": 'LPS22HB'},
                      "time":moment,
                      "fields":{
                              "pression":charge['pression'],
                              "temperature":charge['temperature']                              
                              }
                      }
        elif 'thermometre' in mode:
            charge = {"measurement":"thermometre",
                  "tags":{"sensor": 'SHTC3'},
                  "time":moment,
                  "fields":{
                          "temperature":charge['temperature'],
                          "humidite":charge['humidite']
                          }
                  }
        else:
            logging.warning('Erreur d''info capteur') # raise Exception('Information non prise en charge pour envoi à la base de données')
            return
        self.client.write_points([charge])
