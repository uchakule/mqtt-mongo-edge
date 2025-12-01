# MQTT → Mongo Edge (Demo)

## Prereqs (Windows / Linux)
- Python 3.10+
- MongoDB (local)
- MQTT Broker: Mosquitto (recommended) or any broker

## Setup (local)
1. Clone and create venv:


2. Create `.env` from `.env.example` and set MONGO_URI, MQTT host/port.

### MongoDB (create admin and app user)
If MongoDB is fresh, enable auth and create users. Example (run in `mongo` shell):

## Start services
1. Start subscriber (reads settings and subscribes):
2. Start publisher (in another terminal):
3. (Optional) Start FastAPI UI:


## What to expect
- Publisher publishes JSON every 2s to topic `machine1/process`.
- Subscriber receives messages and stores them to collection `process_data` only when the condition in `Settings` is true (default `alarm1 == True`).
- Use the FastAPI UI to view recent stored documents.

## Run as Windows service (simple with NSSM)
1. Download NSSM.
2. `nssm install EdgeSubscriber` → set Path to python.exe, Arguments to the full path of subscriber_service.py, set working dir and env vars.
3. Start the service through Services.msc or `nssm start EdgeSubscriber`.