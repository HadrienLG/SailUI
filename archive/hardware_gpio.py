# TEST - Hardware
from gpiozero import Button, LED
from time import sleep
from libs.LEDplus import LEDplus

# Initialisation des GPIO
powerLED = LEDplus(16)
green = LEDplus(22)    
red = LEDplus(17)    
yellow1 = LEDplus(23)
yellow2 = LEDplus(24)

powerB = Button(19, hold_time=5) # Si appui 5sec
bouton = Button(26)    

# Allumage des LEDs
leds = [green, red, yellow1, yellow2, powerLED]

for led in leds:
    led.on()
sleep(2)
print('All led should be turned on')
for led in leds:
    led.off()
sleep(2)
print('All led should be turned off')

# Blink
for led in leds:
    led.blink(0.5)
    sleep(1)
print('All led should blink')

# Boutons
def on_press_A():
    print('Button A is pressed')
def on_hold_B():
    print('Button B is hold')
    
bouton.when_pressed = on_press_A
powerB.when_held = on_hold_B
