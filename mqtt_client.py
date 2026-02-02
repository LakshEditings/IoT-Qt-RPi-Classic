import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
LIGHT1_TOPIC = "home/light/light_1"
LIGHT2_TOPIC = "home/light/light_2"  
LIGHT3_TOPIC = "home/light/light_3"  
LIGHT4_TOPIC = "home/light/light_4"  
CURRENT_TOPIC = "home/light/current"

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, 60)
        self.client.subscribe(CURRENT_TOPIC)
        self.client.loop_start()
        self.current_callback = None  # To be set by UI

    def send_light1(self, state):
        self.client.publish(LIGHT1_TOPIC, state)

    def send_light2(self, state):  # New method for second bulb
        self.client.publish(LIGHT2_TOPIC, state)

    def send_light3(self, state):  # New method for second bulb
        self.client.publish(LIGHT3_TOPIC, state)

    def send_light4(self, state):  # New method for second bulb
        self.client.publish(LIGHT4_TOPIC, state)

    def on_message(self, client, userdata, msg):
        if msg.topic == CURRENT_TOPIC and self.current_callback:
            import json
            try:
                data = json.loads(msg.payload.decode())
                # data: {"current":..., "total":...}
                self.current_callback(data)
            except Exception as e:
                print("MQTT parse error:", e)

mqtt_client = MQTTClient()