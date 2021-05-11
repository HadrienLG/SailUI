import subprocess
import json

p =  subprocess.Popen(["systemctl", "status", "--output=json-pretty", 'sailui_server.service'], stdout=subprocess.PIPE)
print(p.stdout.read())