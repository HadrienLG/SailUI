# encoding: utf8

# Objectif : prendre les données du capteur gnss et les diffuser
# Cible : MQTT & BDD
#

# Import
import time
import datetime

from config.logger import gnss_logger
from gpsdclient import GPSDClient
from libs.gnss import format_gnss

from libs.MQTT import MQTT
from libs.database import DataBase

if __name__ == "__main__":
    """
    Lire les données du capteur gnss,
    Les diffuser sur MQTT et la BDD
    """
    # Initialisation
    mqttclient = MQTT()
    bddclient = DataBase(base_name='sensors')
    gnss = GPSDClient(host="127.0.0.1")

    # Boucle
    while True:

        # Récupération des valeurs
        for result in gnss.dict_stream(convert_datetime=True):
            valeurs = format_gnss(result)

            # Logging
            gnss_logger.debug(str(valeurs))

            # MQTT
            basetopic = valeurs['origine']+'/'+valeurs['type']
            for key, value in valeurs.items():
                if key not in ['origine', 'type']:
                    result = mqttclient.publish(basetopic +'/'+ key, value)
                    if result[0] != 0:
                        gnss_logger.exception(f'Echec envoi du message au broker: {basetopic}|{key}->{value}')
                
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
                gnss_logger.exception(f'Echec envoi du message à la base: sensors')

