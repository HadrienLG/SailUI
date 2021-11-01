# encoding: utf8
import paho.mqtt.client as mqtt

class mqttc:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        #self.client.connect("127.0.0.1", 1883, 60)
        #self.client.loop_start()
        self.last_messages = []

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, userdata, flags, rc):
        if rc == 0:
            self.last_messages = 'Connected to MQTT broker successfully!'
        else:
            self.last_messages = "Connected with result code "+mqtt.connack_string(rc)

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("$SYS/#")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, userdata, msg):
        self.last_messages = msg.topic + " " + str(msg.payload)
        pass

    # The callback for when a PUBLISH message is send to the server.
    def on_publish(self, mosq, obj, mid):
        self.last_messages = "Publish mid: " + str(mid)
        pass

if __name__ == '__main__':
    my = mqttc()
    my.client.connect("127.0.0.1", 1883, 60)
    my.client.loop_start()