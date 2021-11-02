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
from sensors.sensors import get_baro, get_gyro, get_therm, get_gnss


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
    db = DataBase()
    main_logger.debug('Base de donnée connectée')

    return sensors, gnss, mqtt, db # Sensors-object

def thread_sensor(func, sensor, q, logger):
    """Generic thread function for sensors

    Args:
        func ([type]): [description]
        sensor ([type]): [description]
        q (Queue.Queue): [description]
        logger (logging.Logger): [description]
    """
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
    t = list(zip(
        [
            (get_therm,sensors['thermometre'],q,logger),
            (get_gyro,sensors['gyroscope'],q,logger),
            (get_baro,sensors['barometre'],q,logger)
        ],
        ['Thermometre', 'Gyroscope', 'Barometre']
    ))
    threads = []
    for capteur in sensors:
        threadObj = Thread( target=thread_sensor, args=capteur[0], name=capteur[1]  )
        threads.append(threadObj)
        threadObj.start()

    # LOOP
    while evisfine:
        for t in threads:
            if not t.is_alive():
                logger.error('Thread '+t.name+' est arrêté')
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
    logger.info(str(rawdatas))

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

    sensors, gnss, mqtt, db = init()
    main_logger.debug('Initialisation des HAT terminée')

    # Process handling for each HAT
    q = Queue()
    pp = zip(
        [processSensors, processGNSS],
        [
            (sensors, sensors_logger, q,),
            (gnss, gnss_logger, q,)
        ],
        ['SENSORS', 'GNSS']
        )
    processes = []
    for p in pp:
        pr = Process(
            target=p[0],
            args=p[1],
            name=p[2]
        )
        pr.start()
        main_logger.debug('Processus '+ p[2] +' lancé')
        proc = dict(zip(
            ['target', 'args', 'name', 'pr', 'pid'],
            [p[0], p[1], p[2]] + [pr, pr.pid]
        ))
        print(proc)
        processes.append(proc)
    
    # LOOP
    while evisfine:
        # Empty Queue -> publish
        output = q.get() # values in Queue are dict
        main_logger.debug('Read Queue, found: ' + str(output))
        if output is not None:
            publish(output, main_logger, mqtt, db)

        # Monitor Process
        for p in processes:
            pr = p['pr']
            if not pr.is_alive():
                main_logger.error(pr.name + '(' + str(pr.pid) + ') is no more alive: ' + str(pr.exitcode))
                # TODO: restart process if possible (check exception)

# Execution
if __name__ == '__main__':
    main()
