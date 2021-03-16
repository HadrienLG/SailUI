import socket
from datetime import datetime
import gpiozero
import time

bouton = gpiozero.Button(26)    

ClientMultiSocket = socket.socket()
host = '127.0.0.1'
port = 10111

def delivermymessage():
    try:
        moment = datetime.now().isoformat()
    except:
        moment = 0
    message = 'Evenement at {}'.format(moment)
    ClientMultiSocket.send(str.encode(message))
    time.sleep(0.5)
    
print('Waiting for connection response')
try:
    ClientMultiSocket.connect((host, port))
except socket.error as e:
    print(str(e))
    
bouton.when_pressed = delivermymessage
while True:
    res = ClientMultiSocket.recv(1024)
    print(res.decode('utf-8'))

ClientMultiSocket.close()