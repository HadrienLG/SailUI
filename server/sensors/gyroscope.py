# encoding: utf8

# Objectif : prendre les données du gyroscope et les diffuser
# Cible : MQTT & BDD
#

# Import
import time
import datetime

from config.logger import sensors_logger
from libs.ICM20948 import ICM20948 # Giroscope
from libs.MQTT import MQTT
from libs.database import DataBase

if __name__ == "__main__":
    """
    Lire les données du gyroscope,
    Les diffuser sur MQTT et la BDD
    """
    # Initialisation
    mqttclient = MQTT()
    bddclient = DataBase(base_name='sensors')
    MotionVal = [0.0 for _ in range(0,9)]
    gyroscope = ICM20948() # Gyroscope

    # Boucle
    while True:

        # Récupération des valeurs
        time.sleep(5) # Une mesure toutes les XX secondes
        gyroscope.icm20948update()
        roll, pitch, yaw = gyroscope.Roll, gyroscope.Pitch, gyroscope.Yaw
        acceleration = gyroscope.Acceleration
        gyroscope = gyroscope.Gyroscope
        magnetic = gyroscope.Magnetic
        
        message = '[GYROSCOPE]\n' + \
                        'Roll = {:.2f}, Pitch = {:.2f}, Yaw = {:.2f}\n'.format(roll, pitch, yaw) + \
                        'Acceleration:  X = {}, Y = {}, Z = {}\n'.format(acceleration[0], acceleration[1], acceleration[2]) + \
                        'Gyroscope:     X = {}, Y = {}, Z = {}\n'.format(gyroscope[0], gyroscope[1], gyroscope[2]) + \
                        'Magnetic:      X = {}, Y = {}, Z = {}'.format(magnetic[0], magnetic[1], magnetic[2])

        valeurs = {
            'origine':'sensors',
            'type':'gyroscope',
            'talker':'ICM20948',
            'Roll': roll, 
            'Pitch': pitch, 
            'Yaw': yaw,
            'Acceleration':acceleration,
            'Gyroscope':gyroscope,
            'Magnetic':magnetic,
            'time':datetime.datetime.now()
        }

        # Logging
        sensors_logger.debug(str(valeurs))

        # MQTT
        basetopic = valeurs['origine']+'/'+valeurs['type']
        for key, value in valeurs.items():
            if key not in ['origine', 'type']:
                result = mqttclient.publish(basetopic +'/'+ key, value)
                if result[0] != 0:
                    sensors_logger.exception(f'Echec envoi du message au broker: {basetopic}|{key}->{value}')
            
        # DataBase
        fields = {key:value for key, value in valeurs.items() if key not in ['origine', 'type', 'talker', 'time']}
        charge = {
            "measurement":valeurs['origine'],
            "tags":{
                "type":valeurs['type'],
                "talker": valeurs['talker'],
                },
            "time":valeurs['time'],
            "fields":fields
        }
        try:
            bddclient.add(charge)
        except:
            sensors_logger.exception(f'Echec envoi du message à la base: sensors')

