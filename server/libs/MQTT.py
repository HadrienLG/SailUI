import paho.mqtt.client as mqtt

class MQTT():    
    def __init__(self, host='localhost', port=1883, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        
        # Création du client
        self.client = mqtt.Client()
                
        # Définition des actions par défaut
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        
        # Connexion
        self.client.connect(host, port, 60)
        self.client.loop_start()
    
    # [MQTT] The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print('Connected to MQTT broker successfully!')
        else:
            print("Connected with result code " + mqtt.connack_string(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("$SYS/#")

    # [MQTT] The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        if self.debug:
            print(msg.topic+" : "+str(msg.payload.decode()))
        pass

    # [MQTT] The callback for when a PUBLISH message is send to the server.
    def on_publish(mosq, obj, mid):
        if self.debug:
            print("Publish mid: " + str(mid))
        pass
    
    # [MQTT] Publish
    def publish(self, sujet, message):
        return self.client.publish(sujet, message)

if __name__ == '__main__':
    mqttclient = MQTT(debug=True)
    