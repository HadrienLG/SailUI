import SHTC3

shtc3 = SHTC3()
while True:
    temperature = therm.SHTC3_Read_Temperature()
    humidite = therm.SHTC3_Read_Humidity()
    print('Temperature = {%6.2}f°C , Humidity = {%6.2}f%%'.format(temperature, humidite))

