# encoding: utf8

# Import
import datetime
from dateutil import parser
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

def format_gnss(charge):
    """[summary]

    Args:
        charge ([dict]): Raw JSON dict send by 

    Returns:
        [type]: [description]
    """
    #TODO: différencier le traitement SKY et TPV

    # Préparation de la charge
    values = {
            'origine':'gnss',
            'type':charge['class'], 
            }
    
    # Spécialisation de la charge
    if charge['class'] == 'TPV': # Temps, Position, Vitesse
        values['talker'] = 'TPV'
        for champ, valeur in charge.items():
            if type(valeur) is float or type(valeur) is str:
                values[champ] = valeur
        if 'lat' in charge.keys():
            values['latitude'] = charge['lat']
        if 'lon' in charge.keys():
            values['longitude'] = charge['lon']
        if 'time' in charge.keys():
            values['datetime'] = parser.parse(charge['time'])
        if 'mode' in charge.keys():
            if charge['mode'] == 0:
                values['fix'] = 'unknown'
            elif charge['mode'] == 1:
                values['fix'] = 'unknown'
            elif charge['mode'] == 2:
                values['fix'] = '2D'
            elif charge['mode'] == 3:
                values['fix'] = '3D'
        if 'status' in charge.keys(): # GPS fix status
            if charge['status'] == 0:
                values['status'] = 'Unknown'
            if charge['status'] == 1:
                values['status'] = 'Normal'
            if charge['status'] == 2:
                values['status'] = 'DGPS'
            if charge['status'] == 3:
                values['status'] = 'RTK Fixed'
            if charge['status'] == 4:
                values['status'] = 'RTK Floating'
            if charge['status'] == 5:
                values['status'] = 'DR'
            if charge['status'] == 6:
                values['status'] = 'GNSSDR'
            if charge['status'] == 7:
                values['status'] = 'Time (surveyed)'
            if charge['status'] == 8:
                values['status'] = 'Simulated'
            if charge['status'] == 9:
                values['status'] = 'P(Y)'

    if charge['class'] == 'SKY': # Satellites en vue
        values['talker'] = 'SKY'
        for champ, valeur in charge.items():
            if type(valeur) is float or type(valeur) is str:
                values[champ] = valeur
        if 'time' in charge.keys():
            values['datetime'] = parser.parse(charge['time'])
        
    return values