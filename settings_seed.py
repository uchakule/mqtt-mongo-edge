# settings_seed.py
import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "edge_db")
SETTINGS_COLLECTION = os.getenv("SETTINGS_COLLECTION", "Settings")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
settings_col = db[SETTINGS_COLLECTION]

doc = {
    "_id": "subscriber_machine_1",
    "name": "machine1_subscriber",
    "broker": {
        "host": os.getenv("MQTT_HOST", "localhost"),
        "port": int(os.getenv("MQTT_PORT", 1883)),
        "username": None,
        "password": None,
        "tls": False
    },
    "client_id": "sub_machine1",
    "subscriptions": [
        {
            "topic": "machine1/process",
            "payload_format": "json",
            "mapping": {
                "temperature": "temperature",
                "alarm1": "alarm1",
                "ID": "ID"
            },
            # Condition supports simple boolean and numeric comparisons:
            # examples: "alarm1 == True", "temperature > 50", "alarm1 == True and temperature > 70"
            "condition": "alarm1 == True"
        }
    ],
    "enabled": True,
    "last_updated": datetime.utcnow().isoformat()
}

# Upsert
settings_col.replace_one({"_id": doc["_id"]}, doc, upsert=True)
print("Settings seeded/updated.")
