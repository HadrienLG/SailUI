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

# Inspiration : https://github.com/PySimpleGUI/PySimpleGUI-Widgets/blob/master/PSG_Widget_psutil_Dashboard.py

import subprocess
import logging
import time
import datetime as dt

import PySimpleGUI as sg
import psutil

from subprocess import check_call

import config.hardware as hardware
from libs.LEDplus import LEDplus
from gpiozero import Button, LED


GRAPH_WIDTH, GRAPH_HEIGHT = 120, 40       # each individual graph size in pixels
ALPHA = .7

def shutdown():
    logging.info('Extinction demandée')
    check_call(['sudo', 'poweroff'])


class DashGraph(object):
    def __init__(self, graph_elem, starting_count, color):
        self.graph_current_item = 0
        self.graph_elem = graph_elem            # type:sg.Graph
        self.prev_value = starting_count
        self.max_sent = 1
        self.color = color
        self.graph_lines = []

    def graph_value(self, current_value):
        delta = current_value - self.prev_value
        self.prev_value = current_value
        self.max_sent = max(self.max_sent, delta)
        percent_sent = 100 * delta / self.max_sent
        line_id = self.graph_elem.draw_line((self.graph_current_item, 0), (self.graph_current_item, percent_sent), color=self.color)
        self.graph_lines.append(line_id)
        if self.graph_current_item >= GRAPH_WIDTH:
            self.graph_elem.delete_figure(self.graph_lines.pop(0))
            self.graph_elem.move(-1, 0)
        else:
            self.graph_current_item += 1
        return delta

    def graph_percentage_abs(self, value):
        self.graph_elem.draw_line((self.graph_current_item, 0), (self.graph_current_item, value), color=self.color)
        if self.graph_current_item >= GRAPH_WIDTH:
            self.graph_elem.move(-1, 0)
        else:
            self.graph_current_item += 1


def human_size(bytes, units=(' bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB')):
    """ Returns a human readable string reprentation of bytes"""
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes >> 10, units[1:])


if __name__ == "__main__":
    # Initialisation
    logging.basicConfig(filename='sailui_monitor.log', level=logging.DEBUG)
    logging.info('Démarrage de SailUI-Monitor, début de journalisation')
    
    powerLED = LEDplus(hardware.leds['power'])
    powerLED.on()
    
    red = LEDplus(hardware.leds['red'])
    
    powerB = Button(hardware.buttons['power'], hold_time=5) # Si appui 5sec
    powerB.when_held = shutdown # Alors déclenchement du signal d'arrêt
    
    # ----------------  Create Window  ----------------
    sg.theme('Black')
    sg.set_options(element_padding=(0, 0), margins=(1, 1), border_width=0)

    def GraphColumn(name, key):
        layout = [
            [sg.Text(name, size=(18,1), font=('Helvetica 8'), key=key+'TXT_')],
            [sg.Graph((GRAPH_WIDTH, GRAPH_HEIGHT),
                      (0, 0),
                      (GRAPH_WIDTH, 100),
                      background_color='black',
                      key=key+'GRAPH_')]]
        return sg.Col(layout, pad=(2, 2))

    red_x = b"R0lGODlhEAAQAPeQAIsAAI0AAI4AAI8AAJIAAJUAAJQCApkAAJoAAJ4AAJkJCaAAAKYAAKcAAKcCAKcDA6cGAKgAAKsAAKsCAKwAAK0AAK8AAK4CAK8DAqUJAKULAKwLALAAALEAALIAALMAALMDALQAALUAALYAALcEALoAALsAALsCALwAAL8AALkJAL4NAL8NAKoTAKwbAbEQALMVAL0QAL0RAKsREaodHbkQELMsALg2ALk3ALs+ALE2FbgpKbA1Nbc1Nb44N8AAAMIWAMsvAMUgDMcxAKVABb9NBbVJErFYEq1iMrtoMr5kP8BKAMFLAMxKANBBANFCANJFANFEB9JKAMFcANFZANZcANpfAMJUEMZVEc5hAM5pAMluBdRsANR8AM9YOrdERMpIQs1UVMR5WNt8X8VgYMdlZcxtYtx4YNF/btp9eraNf9qXXNCCZsyLeNSLd8SSecySf82kd9qqc9uBgdyBgd+EhN6JgtSIiNuJieGHhOGLg+GKhOKamty1ste4sNO+ueenp+inp+HHrebGrefKuOPTzejWzera1O7b1vLb2/bl4vTu7fbw7ffx7vnz8f///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAJAALAAAAAAQABAAAAjUACEJHEiwYEEABniQKfNFgQCDkATQwAMokEU+PQgUFDAjjR09e/LUmUNnh8aBCcCgUeRmzBkzie6EeQBAoAAMXuA8ciRGCaJHfXzUMCAQgYooWN48anTokR8dQk4sELggBhQrU9Q8evSHiJQgLCIIfMDCSZUjhbYuQkLFCRAMAiOQGGLE0CNBcZYmaRIDLqQFGF60eTRoSxc5jwjhACFWIAgMLtgUocJFy5orL0IQRHAiQgsbRZYswbEhBIiCCH6EiJAhAwQMKU5DjHCi9gnZEHMTDAgAOw=="
    layout = [
        [sg.Text('System Status Dashboard'+' '*18),
         sg.Button('', image_data=red_x, button_color=('black', 'black'), key='Exit', tooltip='Closes window')],
        [GraphColumn('Net Out', '_NET_OUT_'),
         GraphColumn('Net In', '_NET_IN_')],
        [GraphColumn('CPU Usage', '_CPU_'),
         GraphColumn('Memory Usage', '_MEM_')],
        [sg.Text('GPS: '),sg.Text('', key='_GPS_STATUS_')],
        [sg.Text('Sensors: '),sg.Text('', key='_SENSOR_STATUS_')],]

    window = sg.Window('PSG System Dashboard', layout,
             keep_on_top=True,
             grab_anywhere=True, no_titlebar=True,
             return_keyboard_events=True, alpha_channel=ALPHA,
             use_default_focus=False, finalize=True)

    # setup graphs & initial values
    netio = psutil.net_io_counters()
    net_in = window['_NET_IN_GRAPH_']
    net_graph_in = DashGraph(net_in, netio.bytes_recv, '#23a0a0')
    net_out = window['_NET_OUT_GRAPH_']
    net_graph_out = DashGraph(net_out, netio.bytes_sent, '#56d856')

    cpu_usage_graph = DashGraph(window['_CPU_GRAPH_'], 0, '#d34545')
    mem_usage_graph = DashGraph(window['_MEM_GRAPH_'], 0, '#BE7C29')
    
    # systemd status
    last_check = dt.datetime.now()

    # print(psutil.cpu_percent(percpu=True))
    # ----------------  main loop  ----------------
    while True :
        # --------- Read and update window once a second--------
        event, values = window.read(timeout=1000)
        # Be nice and give an exit, expecially since there is no titlebar
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        # ----- Network Graphs -----
        netio = psutil.net_io_counters()
        write_bytes = net_graph_out.graph_value(netio.bytes_sent)
        read_bytes = net_graph_in.graph_value(netio.bytes_recv)
        window['_NET_OUT_TXT_'].update('Net out {}'.format(human_size(write_bytes)))
        window['_NET_IN_TXT_'].update('Net In {}'.format(human_size(read_bytes)))
        # ----- CPU Graph -----
        cpu = psutil.cpu_percent(0)
        cpu_usage_graph.graph_percentage_abs(cpu)
        window['_CPU_TXT_'].update('{0:2.0f}% CPU Used'.format(cpu))
        # ----- Memory Graph -----
        mem_used = psutil.virtual_memory().percent
        mem_usage_graph.graph_percentage_abs(mem_used)
        window['_MEM_TXT_'].update('{}% Memory Used'.format(mem_used))

        # Vérification des status des services systemd
        mes_services = ['sailui_publish_gps.service', 'sailui_publish_sensors.service']
        if (dt.datetime.now() - last_check < dt.timedelta(seconds=5)):
            for ind, service in enumerate(mes_services):
                p =  subprocess.Popen(["systemctl", "status", service], stdout=subprocess.PIPE)
                raw = p.stdout.read().decode()
                status = [x.strip() for x in raw.split('\n')]
                if 'active' == status[2].split(' ')[1]:
                    if ind == 0:
                        window['_GPS_STATUS_'].update('OK')
                    if ind == 1:
                        window['_SENSOR_STATUS_'].update('OK')
                    pass
                else:
                    logging.error(raw)
                    red.on()
                    if ind == 0:
                        window['_GPS_STATUS_'].update('erreur')
                    if ind == 1:
                        window['_SENSOR_STATUS_'].update('erreur')
            
