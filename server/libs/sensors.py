# encoding: utf8

# Import
import time
import datetime
import logging

# Functions

def get_gyro(gyro):
    """Ask gyroscope for fresh values

    Args:
        gyro ([type]): [description]

    Returns:
        dict: raw values
    """
    # Gyroscope
    gyro.icm20948update()
    roll, pitch, yaw = gyro.Roll, gyro.Pitch, gyro.Yaw
    acceleration = gyro.Acceleration
    gyroscope = gyro.Gyroscope
    magnetic = gyro.Magnetic
    
    message = '[GYROSCOPE]\n' + \
                    'Roll = {:.2f}, Pitch = {:.2f}, Yaw = {:.2f}\n'.format(roll, pitch, yaw) + \
                    'Acceleration:  X = {}, Y = {}, Z = {}\n'.format(acceleration[0], acceleration[1], acceleration[2]) + \
                    'Gyroscope:     X = {}, Y = {}, Z = {}\n'.format(gyroscope[0], gyroscope[1], gyroscope[2]) + \
                    'Magnetic:      X = {}, Y = {}, Z = {}'.format(magnetic[0], magnetic[1], magnetic[2])

    values = {
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
    return values

def get_baro(baro, rate=5):
    """Ask barometer for fresh values
    Interval: to be defined, default 5s

    Args:
        baro ([type]): [description]

    Returns:
        dict: raw values
    """
    # Baromètre
    time.sleep(rate)
    baro.update()

    values = {
        'origine':'sensors',
        'type':'barometre',
        'talker':'LPS22HB',
        'pression':baro.PRESS_DATA,
        'temperature':baro.TEMP_DATA,
        'time':datetime.datetime.now()
        }
    return values

def get_therm(therm, rate=1):
    """Ask thermometer for fresh values
    Interval: to be defined, default 1s

    Args:
        therm ([type]): [description]

    Returns:
        dict: raw values
    """
    # Thermomètre
    time.sleep(rate)
    temperature, humidite = therm.measurements

    values = {
        'origine':'sensors',
        'type':'thermometre',
        'talker':'SHTC3',
        'temperature':temperature,
        'humidite':humidite,
        'time':datetime.datetime.now(),
        }
    return values


