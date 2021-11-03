# encoding: UTF-8

# README
"""

"""

# Import
from multiprocessing import Queue, Process
from threading import Thread
import busio
import board
import serial
import pynmea2
import os
import sys

# Custom
from sensors.mqttc import mqttc
from database import DataBase
from logger import main_logger, gnss_logger, sensors_logger

# Sensors
import adafruit_shtc3
from sensors.AD import ADS1015 # Amplificateur de gain
from sensors.ICM20948 import ICM20948 # Giroscope
from sensors.LPS22HB import LPS22HB # Pression, température
from sensors.TCS34725 import TCS34725 # Couleurs
from sensors.mqttc import mqttc #from sensors.SHTC3 import SHTC3 # Température, humidité
from sensors.sensors import get_baro, get_gyro, get_therm
from sensors.gnss import get_gnss


# Parameters
main_logger.info("Lancement de l'application")
evisfine = True # Everything is fine, so far

# Functions
def init():
    """ Initialisation des composants

    Returns:
        [type]: [description]
    """

    # Initialisation des capteurs
    # - gyroscope : icm20948
    # - Baromètre : lps22hb
    # - Thermomètre : shtc3
    main_logger.debug('Initialisation des capteurs')
    i2c = busio.I2C(board.SCL, board.SDA)
    MotionVal = [0.0 for _ in range(0,9)]
    icm20948 = ICM20948() # Gyroscope
    lps22hb = LPS22HB() # Pression/température
    shtc3 = adafruit_shtc3.SHTC3(i2c) # Température/humidité
    
    sensors = {'gyroscope':icm20948,'barometre':lps22hb,'thermometre':shtc3}
    
    # GNSS
    port = "/dev/serial0"
    gnss = serial.Serial(port, baudrate = 9600, timeout = 0.5)
    main_logger.debug('Port série ouvert')

    # MQTT
    mqtt = mqttc()
    mqtt.client.connect("127.0.0.1", 1883, 60)
    mqtt.client.loop_start()
    main_logger.debug('Client MQTT connecté')
    
    # InfluxDB
    dbs = {'sensors':DataBase(base_name='sensors'), 'gnss':DataBase(base_name='gnss')}
    main_logger.debug('Bases de données connectées')
    for db in dbs.values():
        main_logger.debug(str(db.info()))

    return sensors, gnss, mqtt, dbs # Sensors-object

def thread_sensor(func, sensor, q, logger):
    """Generic thread function for sensors

    Args:
        func ([type]): [description]
        sensor ([type]): [description]
        q (Queue.Queue): [description]
        logger (logging.Logger): [description]
    """
    logger.info('Démarrage du thread...')
    while evisfine:
        values = func(sensor)
        q.put(values)
        logger.debug(str(values))
        
def processSensors(sensors, logger, q):
    """Multithread sensors datas handling

    Args:
        sensors ([type]): [description]
        logger ([type]): [description]
        q ([type]): [description]
    """

    # Thread handling for each sensors
    parametres = list(zip(
        [
            (get_therm,sensors['thermometre'],q,logger),
            (get_gyro,sensors['gyroscope'],q,logger),
            (get_baro,sensors['barometre'],q,logger)
        ],
        ['Thermometre', 'Gyroscope', 'Barometre']
    ))
    threads = []
    for parametre in parametres:
        threadObj = Thread( target=thread_sensor, args=parametre[0], name=parametre[1]  )
        threads.append(threadObj)
        threadObj.start()
        logger.debug(f'Thread {threadObj.getName()} est démarré')
        
    for th in threads:
        th.join()
        logger.debug(f'Thread {th.getName()} est joint')

    # LOOP
    while evisfine:
        for th in threads:
            if not th.is_alive():
                logger.error('Thread '+th.getName()+' est arrêté')
                # TODO: try to restart thread (check exception)

def processGNSS(gnss, logger, q):
    """Read serial output from M8Q and add datas to Queue

    Args:
        gnss (serial.Serial): [description]
        logger (logging.Logger): [description]
        q (Queue.Queue): [description]
    """ 
    while evisfine:
        values = get_gnss(gnss)
        q.put(values)
        logger.debug(str(values))


def publish(rawdatas, logger, mqtt, db):
    """Send values from HAT to MQTT broker, log entries and database

    Args:
        rawdatas ([type]): [description]
    """
    # Logging
    logger.debug(str(rawdatas))

    # MQTT
    basetopic = rawdatas['origine']+'/'+rawdatas['type']
    for key, value in rawdatas.items():
        if key not in ['origine', 'type']:
            result = mqtt.client.publish(basetopic +'/'+ key, value)
            if result[0] != 0:
                logger.exception(f'Echec envoi du message au broker: {basetopic}|{key}->{value}')
        
    # DataBase
    fields = {key:value for key, value in rawdatas.items() if key not in ['origine', 'type', 'talker', 'time']}
    charge = {
        "measurement":rawdatas['origine'],
        "tags":{
            "type":rawdatas['type'],
            "talker": rawdatas['talker'],
            },
        "time":rawdatas['time'],
        "fields":fields
    }
    db.add(charge)

# Main
def main():
    """Gestion des senseurs vers l'assistance à la navigation
    """
    # Init

    sensors, gnss, mqtt, dbs = init()
    main_logger.debug('Initialisation des HAT terminée')

    # Process handling for each HAT
    q = Queue()
    parametres = zip(
        [processSensors, processGNSS],
        [
            (sensors, sensors_logger, q,),
            (gnss, gnss_logger, q,)
        ],
        ['SENSORS', 'GNSS']
        )
    # pp = [[processSensors, (sensors, sensors_logger, q,), 'SENSORS']] # For debug purpose
    processes = []
    for parametre in parametres:
        pr = Process(
            target=parametre[0],
            args=parametre[1],
            name=parametre[2]
        )
        pr.start()
        main_logger.debug('Processus '+ parametre[2] +' lancé')
        proc = dict(zip(
            ['target', 'args', 'name', 'pr', 'pid'],
            [parametre[0], parametre[1], parametre[2]] + [pr, pr.pid]
        ))
        processes.append(proc)
    
    # LOOP
    while evisfine:
        # Empty Queue -> publish
        output = q.get() # values in Queue are dict
        if output is not None:
            if output['origine'] == 'sensors':
                publish(output, sensors_logger, mqtt, dbs['sensors'])
            if output['origine'] == 'gnss':
                publish(output, gnss_logger, mqtt, dbs['gnss'])    

        # Monitor Process
        for p in processes:
            pr = p['pr']
            if not pr.is_alive():
                main_logger.error(pr.name + '(' + str(pr.pid) + ') is no more alive: ' + str(pr.exitcode))
                # TODO: restart process if possible (check exception)

# Execution
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
