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

# Import
import datetime
import logging
import pynmea2
from influxdb import InfluxDBClient,exceptions

# Class

class DataBase():
    def __init__(self, base_name='position'):
        self.client = InfluxDBClient(host='localhost', port=8086)
        logging.info(self.client.get_list_database())

        if base_name in [list(x.values())[0] for x in self.client.get_list_database()]:
             logging.info(f'Base de données {base_name} disponible')
        else:
            self.client.create_database(base_name)
            logging.info(f'Base de données {base_name} créée')
        self.client.switch_database(base_name)

    def add(self, charge):
        self.client.write_points([charge])
        logging.debug('Charge '+str(charge)+' ajoutée à la base'.format(self.client))

