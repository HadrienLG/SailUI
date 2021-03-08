# https://gpiozero.readthedocs.io/en/stable/recipes.html#pin-numbering
# https://www.raspberrypi.org/documentation/usage/gpio/python/README.md

from gpiozero import LED, Button
from time import sleep
from signal import pause

ledG = LED(22)
ledR = LED(17)
ledY1 = LED(23)
ledY2 = LED(24)
ledL = LED(16)

buttonS1 = Button(26)
buttonS2 = Button(19)

# Affectation
buttonS1.when_pressed = ledG.on
buttonS1.when_released = ledG.off

buttonS2.when_pressed = ledR.on
buttonS2.when_released = ledR.off

# Test
myleds = [ledG, ledR, ledY1, ledY2, ledL]
for myled in myleds:
    myled.on()
    sleep(0.5)
    myled.off()
    sleep(0.2)
    
pause()