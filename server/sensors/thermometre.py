# encoding: utf8

# Objectif : prendre les données du thermometre et les diffuser
# Cible : MQTT & BDD
#

# Import
import time
import datetime
import busio
import board

from config.logger import sensors_logger
import adafruit_shtc3 #from sensors.SHTC3 import SHTC3 # Température, humidité
from libs.MQTT import MQTT
from libs.database import DataBase

if __name__ == "__main__":
    """
    Lire les données du thermomètre,
    Les diffuser sur MQTT et la BDD
    """

    # Initialisation
    mqttclient = MQTT()
    bddclient = DataBase(base_name='sensors')
    i2c = busio.I2C(board.SCL, board.SDA)
    thermometre = adafruit_shtc3.SHTC3(i2c)

    # Boucle
    while True:

        # Récupération des valeurs
        time.sleep(5) # Une mesure toutes les XX secondes
        temperature, humidite = thermometre.measurements

        valeurs = {
            'origine':'sensors',
            'type':'thermometre',
            'talker':'SHTC3',
            'temperature':temperature,
            'humidite':humidite,
            'time':datetime.datetime.now(),
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

