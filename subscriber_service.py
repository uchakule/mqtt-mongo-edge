# subscriber_service.py
import os
import time
import json
import threading
from datetime import datetime
from pymongo import MongoClient
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import ast

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "edge_db")
SETTINGS_COLLECTION = os.getenv("SETTINGS_COLLECTION", "Settings")
DATA_COLLECTION = os.getenv("DATA_COLLECTION", "process_data")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

# --- Mongo setup
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
settings_col = db[SETTINGS_COLLECTION]
data_col = db[DATA_COLLECTION]

# --- AST-based safety for condition evaluation
ALLOWED_AST_NODES = (
    ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp,
    ast.Compare, ast.Call, ast.Name, ast.Load, ast.Constant,
    ast.And, ast.Or, ast.Not,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
)

def is_safe_expr(expr: str) -> bool:
    try:
        tree = ast.parse(expr, mode='eval')
    except Exception:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_AST_NODES):
            return False
    return True

def safe_eval(expr: str, payload: dict) -> bool:
    # Normalize booleans
    expr_norm = expr.replace('true', 'True').replace('false', 'False')

    if not is_safe_expr(expr_norm):
        raise ValueError("Unsafe or unsupported condition expression")

    # compile and evaluate using payload as locals (no globals)
    try:
        result = eval(compile(ast.parse(expr_norm, mode='eval'), '<string>', 'eval'), {}, payload)
        return bool(result)
    except Exception as e:
        print("Condition eval error:", e)
        return False

# --- Subscriber class which reads settings and subscribes dynamically
class MQTTSubscriber:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.subscriptions = {}  # topic -> config dict
        self._load_settings()

    def _load_settings(self):
        # Fetch enabled settings
        settings = settings_col.find({"enabled": True})
        subs = {}
        for s in settings:
            for sub in s.get("subscriptions", []):
                topic = sub.get("topic")
                if topic:
                    subs[topic] = {
                        "condition": sub.get("condition"),
                        "mapping": sub.get("mapping", {}),
                        "settings_id": s.get("_id")
                    }
        self.subscriptions = subs
        print("Loaded subscriptions:", list(self.subscriptions.keys()))

    def connect_and_start(self):
        # Connect to broker
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)
        # subscribe to all topics from settings
        for topic in self.subscriptions.keys():
            self.client.subscribe(topic)
            print("Subscribed to:", topic)
        # Start network loop in background
        self.client.loop_start()

        # Also start a watcher thread to reload settings periodically (e.g., every 30s)
        t = threading.Thread(target=self._watch_settings_loop, daemon=True)
        t.start()

    def _watch_settings_loop(self):
        while True:
            time.sleep(30)
            self._load_settings()
            # ensure subscribed to any new topics
            for topic in self.subscriptions.keys():
                self.client.subscribe(topic)

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with rc=", rc)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as e:
            print("Invalid JSON payload:", e)
            return

        topic = msg.topic
        cfg = self.subscriptions.get(topic)
        if not cfg:
            print("No config for topic", topic)
            return

        condition = cfg.get("condition")
        mapping = cfg.get("mapping", {})
        # Build a locals dict for condition evaluation by mapping keys to payload values
        locals_for_eval = {}
        # Put payload values directly; mapping may rename fields if needed
        for src_key, dst_key in mapping.items():
            value = payload.get(src_key)
            locals_for_eval[dst_key] = value

        # Also put all payload keys as-is for flexibility
        for k, v in payload.items():
            if k not in locals_for_eval:
                locals_for_eval[k] = v

        should_store = True
        if condition:
            try:
                should_store = safe_eval(condition, locals_for_eval)
            except Exception as e:
                print("Error evaluating condition:", e)
                should_store = False

        print(f"Received topic={topic} payload={payload} -> condition={condition} -> {should_store}")

        if should_store:
            doc = {
                "topic": topic,
                "payload": payload,
                "received_at": datetime.utcnow()
            }
            try:
                data_col.insert_one(doc)
                print("Inserted document into MongoDB.")
            except Exception as e:
                print("Mongo insert error:", e)

def main():
    sub = MQTTSubscriber()
    sub.connect_and_start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping subscriber...")
    finally:
        sub.client.loop_stop()
        sub.client.disconnect()

if __name__ == "__main__":
    main()
