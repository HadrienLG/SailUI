# encoding: utf8

# Objectif : prendre les données du capteur de pression et les diffuser
# Cible : MQTT & BDD
#

# Import
import time
import datetime

from config.logger import sensors_logger
from libs.LPS22HB import LPS22HB # Pression, température
from libs.MQTT import MQTT
from libs.database import DataBase

if __name__ == "__main__":
    """
    Lire les données du capteur de pression,
    Les diffuser sur MQTT et la BDD
    """
    # Initialisation
    mqttclient = MQTT()
    bddclient = DataBase(base_name='sensors')
    barometre = LPS22HB()

    # Boucle
    while True:

        # Récupération des valeurs
        time.sleep(5) # Une mesure toutes les XX secondes
        barometre.update()
        valeurs = {
            'origine':'sensors',
            'type':'barometre',
            'talker':'LPS22HB',
            'pression':barometre.PRESS_DATA,
            'temperature':barometre.TEMP_DATA,
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

