import os

import motor.motor_asyncio


def get_mongodb_string():
    username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    url = os.getenv("MONGO_HOST", "mongo")
    port = os.getenv("MONGO_PORT", 27017)
    return f"mongodb://{username}:{password}@{url}:{port}/"


mongo_client = motor.motor_asyncio.AsyncIOMotorClient(get_mongodb_string())

db = mongo_client.detections
