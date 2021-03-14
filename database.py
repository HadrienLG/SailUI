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

# Other Libs
import pynmea2
from influxdb import InfluxDBClient,exceptions


class DataBase():
    def __init__(self, base_name='position'):
        self.client = InfluxDBClient(host='localhost', port=8086)
        all_influxDB = self.client.get_list_database()
        if base_name in [list(x.values())[0] for x in self.client.get_list_database()]:
             print('Base de données {} disponible'.format(base_name))
        else:
            self.client.create_database(base_name)
            print('Base de données {} créée'.format(base_name))
        self.client.switch_database(base_name)

    def add_point(nmea_phrase):
        message = pynmea2.parse(phrase)
        msg = dict(zip([x[0] for x in message.fields], message.data))
        valid = (message.latitude != 0 and message.longitude != 0)
        if message.XX == 'RMC' and valid:
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
        elif message.XXX == "GLL" and valid:
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
        else:
            return
        self.client.write_points([charge])
