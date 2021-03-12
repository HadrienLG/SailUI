import socket
import sys
import datetime
from gpiozero import Button
from time import sleep

# Socket
port = 10111
size = 1024
s = None
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostname()
    s.connect(('127.0.0.1', port))
except socket.error as e:
    if s:
        s.close()
    print(f"Could not open socket: {e}")
    sys.exit(1)

# Premier contact
data = str.encode("> Hello server, I'm client")
s.sendall(data)


def button_callback():
    message = "[{}] Button was pushed!".format(str(datetime.datetime.now()))
    print(message)
    s.send(message.encode())    
    sleep(0.2)

# Bouton
# GPIO | o o x o o o o o o ...
#      | o x o o o o o o o ...
button = Button(26)
button.when_pressed = button_callback


# Réception des messages
while True:    
    data = s.recv(size)
    message = data.decode('UTF-8')
    print(f"Socket: {message}")
s.close()
