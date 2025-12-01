# fastapi_app.py
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "edge_db")
SETTINGS_COLLECTION = os.getenv("SETTINGS_COLLECTION", "Settings")
DATA_COLLECTION = os.getenv("DATA_COLLECTION", "process_data")

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
settings_col = db[SETTINGS_COLLECTION]
data_col = db[DATA_COLLECTION]

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # Serve a simple page that will poll stored docs
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/settings")
def list_settings():
    docs = list(settings_col.find({}, {"_id": 1, "name": 1, "enabled": 1}))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs

@app.get("/api/data")
def get_data(limit: int = 50):
    docs = list(data_col.find({}, sort=[("received_at", -1)]).limit(limit))
    for d in docs:
        d["_id"] = str(d["_id"])
        if "received_at" in d:
            d["received_at"] = d["received_at"].isoformat()
    return docs
