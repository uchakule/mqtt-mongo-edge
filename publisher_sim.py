# publisher_sim.py
import time
import json
import random
import os
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv()

BROKER_HOST = os.getenv("MQTT_HOST", "localhost")
BROKER_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC = "machine1/process"

def make_payload():
    payload = {
        "temperature": round(random.uniform(20.0, 90.0), 2),
        "alarm1": random.choice([True, False]),
        "ID": "MACHINE_001"
    }
    return payload

def main():
    client = mqtt.Client("publisher_sim_1")
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()
    try:
        while True:
            payload = make_payload()
            client.publish(TOPIC, json.dumps(payload))
            print("Published:", payload)
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopping publisher")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
