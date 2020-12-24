import socket
import sys

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

# Réception des messages
while True:    
    data = s.recv(size)
    message = data.decode('UTF-8')
    print(f"NMEA: {message}")
s.close()