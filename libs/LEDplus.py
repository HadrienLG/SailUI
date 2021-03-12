from gpiozero import LED
import time
import threading

class LEDplus():
    def __init__(self,pinnumber):
        self.led = LED(pinnumber)
        self.__loop = True
        self.__threading = threading.Thread(target=self.__blink)
        self.state = 'Off'
        self.pitch = 10

    def on(self,):
        self.__loop = False
        self.maybejoin()
        self.led.on()
        self.state = 'On'

    def off(self, ):
        self.__loop = False
        self.maybejoin()
        self.led.off()
        self.state = 'Off'
        
    def train(self, num):
        self.__loop = False
        self.maybejoin()
        
        previous_state = self.state
        self.state = 'Train'
        
        # Boucle
        self.__loop = False
        self.off()
        time.sleep(0.8)
        for _ in range(0,2):
            for _ in range(0,num):
                self.on()
                time.sleep(0.2)
                self.off()
                time.sleep(0.2)
            time.sleep(0.8)
        # Retour à l'état précédent
        if previous_state == 'Blink':
            self.blink(self.pitch)
        elif previous_state == 'On':
            self.on()
        else:
            self.off()

    def maybejoin(self,):
        if self.__threading.isAlive():
            self.__threading.join()

    def blink(self, pitch):
        self.__threading = threading.Thread(target=self.__blink, args=(pitch, ))
        self.__threading.start()
        self.pitch = pitch
        self.state = 'Blink'

    def __blink(self, pitch=.25):
        self.__loop = True
        while self.__loop:
            self.led.toggle()
            time.sleep(pitch/2)
        self.led.off()
        

if __name__ == "__main__":
    pin = input('Which pin is your LED on?')
    myled = LEDplus(int(pin))
    
    myled.on()
    print('LED is on...')
    time.sleep(2)
    
    myled.off()
    print('LED is off')
    time.sleep(1)
    
    for pitch in [0.25, 0.5, 1, 2]:
        myled.blink(pitch)
        print('Blink, pitch :',pitch)
        time.sleep(3)
    print('End of LEDplus')
