import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT = 1883
LIGHT1_TOPIC = "home/light/light_1"
LIGHT2_TOPIC = "home/light/light_2"  
LIGHT3_TOPIC = "home/light/light_3"  
LIGHT4_TOPIC = "home/light/light_4"  
ENERGY_TOPIC = "home/light/energy"  # New dual-sensor topic

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, 60)
        self.client.subscribe(ENERGY_TOPIC)  # Subscribe to new energy topic
        self.client.loop_start()
        self.energy_callback = None  # Callback for Screen2
        self.motion_callback = None  # Callback for motion status

    def send_light1(self, state):
        # Invert logic: UI "ON" → send "OFF", UI "OFF" → send "ON"
        inverted_state = "OFF" if state == "ON" else "ON"
        self.client.publish(LIGHT1_TOPIC, inverted_state)

    def send_light2(self, state):
        inverted_state = "OFF" if state == "ON" else "ON"
        self.client.publish(LIGHT2_TOPIC, inverted_state)

    def send_light3(self, state):
        inverted_state = "OFF" if state == "ON" else "ON"
        self.client.publish(LIGHT3_TOPIC, inverted_state)

    def send_light4(self, state):
        inverted_state = "OFF" if state == "ON" else "ON"
        self.client.publish(LIGHT4_TOPIC, inverted_state)

    def on_message(self, client, userdata, msg):
        if msg.topic == ENERGY_TOPIC and self.energy_callback:
            import json
            try:
                data = json.loads(msg.payload.decode())
                # ESP32 sends: {"L1":{...}, "L2":{...}, "motionActive":1, ...}
                self.energy_callback(data)
                
                # Also handle motion status if callback exists
                if hasattr(self, 'motion_callback') and self.motion_callback:
                    motion_data = {
                        "motion_enabled": data.get("motionEnabled", 0),
                        "motion_active": data.get("motionActive", 0)
                    }
                    self.motion_callback(motion_data)
            except Exception:
                # Silently ignore parse errors
                pass
            
    def send_override_light1(self):
        self.client.publish("home/light/override_light1", "bypass")

mqtt_client = MQTTClient()