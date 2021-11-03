# encoding: utf8

# Import
import datetime
import logging
import pynmea2
import subprocess

# Parameters
identifiants = ['GGA', 'GLL', 'GSA', 'GSV', 'VTG', 'RMC'] # Worthy

# Functions

def get_gnss(gnss):
    """Ask M8Q GNSS chip for fresh values

    Args:
        gnss ([type]): [description]

    Returns:
        dict: raw values
    """
    # Lecture d'une ligne et décodage
    ligne = gnss.readline()
    phrase = ligne.decode("utf-8")
    
    # Si la phrase NMEA nous intéresse, on la traite
    id_nmea = phrase[3:6]
    if id_nmea in identifiants:                    
        # Extrait des phrases NMEA
        nmea = pynmea2.parse(phrase)
        identifier = nmea.identifier()[2:-1]
        
        # Cas général
        values = {
            'origine':'gnss',
            'type':identifier, 
            'talker':nmea.talker,
            'time':0#nmea.datetime.isoformat()
            }
        for champ, valeur in dict(zip(nmea.fields,nmea.data)).items():
            cle = champ[1].strip().replace(' ','_')
            values[cle] = valeur
        
        # Cas particulier
        if identifier == 'RMC':
            values["latitude"] = nmea.latitude
            values["longitude"] = nmea.longitude
            values["heading"] = nmea.data[7]
        if identifier == 'VTG':
            values["speed"] = nmea.data[4] # 'Speed over ground knots'
            values["heading"] = nmea.data[0] # 'True Track made good'
        if identifier == 'GGA':
            values["date"] = nmea.data[0] # 'TimeStamp'
            values["sats"] = nmea.data[6] # 'Number of Satellites in use'
            values["altitude"] = nmea.data[8] # 'Antenna Alt above sea level (mean)'
        if identifier == 'GLL':
            values["latitude"] = nmea.latitude
            values["longitude"] = nmea.longitude
        if identifier == 'GSA':
            pass
        if identifier == 'GSV':
            pass

        # Mise à l'heure du système
#         try:
#             system_time = datetime.datetime.now()
#             gps_time = nmea.datetime.isoformat()
#             logging.debug(f'Heures: system={system_time}, gps={gps_time}')
#             if datetime.timedelta(system_time, gps_time)>0:
#                 new_time = gps_time.strftime('%y-%m-%d %H:%M:%S')
#                 cmd = f'sudo date -s "{new_time}"'
#                 subprocess.call(cmd)
#         except:
#             pass

        # Return
        return values