"""
TODO:
Develop the following features:

Integrate Swagger.
Implement JWT for authentication.
POST /users to create the users.
Develop GET /detections endpoint to expose all detections indexed in the database you chose in Indexer Microservice:
The response should be paginated. Use skip and limit as the pagination query params.
Develop GET /stats to return vehicle counting per Make (group_by).
Develop GET /alerts endpoint to receive the alerts in real-time:
This endpoint should be an event stream.
Develop a Kafka Consumer inside the API to consume the alerts and expose them through the /alerts event-stream endpoint.

Decisions:
- Use fastAPI
- Use mongodb
- Use swagger.
- pytest for testing.

"""
import asyncio
import json
import os
import logging
import time
from typing import Optional, List

from fastapi import FastAPI, Body, status, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer, errors
from sse_starlette.sse import EventSourceResponse

from models import VehicleDetectionModel
from db import db

STREAM_DELAY = 1
RETRY_TIMEOUT = 15000  # millisecond
KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
DETECTIONS_TOPIC = os.environ.get("DETECTIONS_TOPIC")
KAFKA_TIMEOUT = os.environ.get("KAFKA_TIMEOUT", 120)

app = FastAPI()


def build_consumer():
    try:
        return KafkaConsumer(
            DETECTIONS_TOPIC,
            bootstrap_servers=[KAFKA_BROKER_URL],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode())
        )
    except errors.NoBrokersAvailable:
        return None


@app.on_event("startup")
async def startup_event():
    must_end = time.time() + KAFKA_TIMEOUT
    while (consumer := build_consumer()) is None and time.time() < must_end:
        # waiting for kafka broker services
        time.sleep(1)

    if consumer is None:
        logging.error("Timeout waiting for kafka broker. Exit!")
        exit(1)


@app.get(
    "/detections",
    response_description="List all vehicles detections",
    response_model=List[VehicleDetectionModel]
)
async def detections():
    data = await db["vehicles"].find().to_list(1000)
    return data


@app.get('/alerts')
async def alerts_stream(request: Request):
    def new_messages():
        # Add logic here to check for new messages
        yield 'Hello World'

    async def event_generator():
        while True:
            # If client closes connection, stop sending events
            if await request.is_disconnected():
                break
            while (message := next(consumer)) is not None:
                vehicle = VehicleDetectionModel(**message.value)
                if vehicle.category.upper() == SUSPICIOUS_VEHICLE.upper():
                    alert_producer.send(ALERTS_TOPIC, value=vehicle)
                await db.vehicles.insert_one(vehicle.dict())
            # Checks for new messages and return them to client if any
            if new_messages():
                yield {
                        "event": "new_message",
                        "id": "message_id",
                        "retry": RETRY_TIMEOUT,
                        "data": "message_content"
                }

            await asyncio.sleep(STREAM_DELAY)

    return EventSourceResponse(event_generator())
#
#
# @app.get(
#     "/{address}/{key}", response_description="Get a single item by key", response_model=ItemModel
# )
# async def show_item(address: str, key: str):
#     if (wallet := await db["wallets"].find_one({"address": address})) is not None:
#         if (item := next(filter(lambda i: i.get("key") == key, wallet.get("items", [])), None)) is not None:
#             return item
#         else:
#             raise HTTPException(status_code=404, detail=f"Item {key} not found")
#     raise HTTPException(status_code=404, detail=f"Wallet {address} not found")
#
#
# @app.post("/", response_description="Add new wallet", response_model=WalletModel)
# async def create_wallet(wallet: WalletModel = Body(...)):
#     # TODO: check for existing wallet with same address
#     _wallet = jsonable_encoder(wallet)
#     _wallet = await db["wallets"].insert_one(_wallet)
#     new_wallet = await db["wallets"].find_one({"_id": _wallet.inserted_id})
#     return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_wallet)
#
#
# @app.put("/{address}", response_description="Update a wallet", response_model=WalletModel)
# async def update_wallet(address: str, wallet: WalletModel = Body(...)):
#     _wallet = {k: v for k, v in wallet.dict().items() if v is not None}
#
#     if len(_wallet) >= 1:
#         update_result = await db["wallets"].update_one({"address": address}, {"$set": _wallet})
#
#         if update_result.modified_count == 1:
#             if (
#                 updated_wallet := await db["wallets"].find_one({"address": address})
#             ) is not None:
#                 return updated_wallet
#
#     if (existing_wallet := await db["wallets"].find_one({"address": address})) is not None:
#         return existing_wallet
#
#     raise HTTPException(status_code=404, detail=f"Wallet {address} not found")
#
#
# @app.post("/new", response_description="Create name for wallet", response_model=NameWalletModel)
# async def create_name(name_wallet: NameWalletModel = Body(...)):
#     # TODO: check for existing name wallet with same address
#     _name = jsonable_encoder(name_wallet)
#     _name = await db["names"].insert_one(_name)
#     new_name = await db["names"].find_one({"_id": _name.inserted_id})
#     return JSONResponse(status_code=status.HTTP_201_CREATED, content=new_name)
