"""
API of vehicle detections solution
"""
import asyncio
import json
import os
import time
from typing import List

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, Body, status, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from models import VehicleDetectionModel
from db import db

PROJECT_NAME = "VehicleDetection"
KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
ALERTS_TOPIC = os.environ.get("ALERTS_TOPIC")
KAFKA_TIMEOUT = int(os.environ.get("KAFKA_TIMEOUT", 120))
ALERT_GROUP = os.environ.get("ALERT_GROUP", "alerts")

app = FastAPI(title=PROJECT_NAME)


@app.on_event("startup")
async def startup_event():
    """We try to connect to kafka broker, before to start up api server"""
    loop = asyncio.get_event_loop()
    must_end = time.time() + KAFKA_TIMEOUT
    connected = False
    while time.time() < must_end and not connected:
        try:
            _consumer = AIOKafkaConsumer(
                ALERTS_TOPIC,
                loop=loop,
                bootstrap_servers=[KAFKA_BROKER_URL],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda value: json.loads(value.decode())
            )
            await _consumer.start()
            await _consumer.stop()
            print("Connected to kafka broker!")
            connected = True
        except Exception as ex:
            print("Unable to connect to kafka. Waiting...", ex, type(ex))
            await asyncio.sleep(1)


@app.get(
    "/detections",
    response_description="List all vehicles detections",
    response_model=List[VehicleDetectionModel]
)
async def detections(skip: int = 0, limit: int = 100):
    data = await db["vehicles"].find().skip(skip).to_list(limit)
    return data


@app.get('/alerts')
async def alerts_stream(request: Request):

    async def event_generator(consumer):
        try:
            # Consume messages
            async for msg in consumer:
                # If client was closed the connection
                if await request.is_disconnected():
                    break
                alert = VehicleDetectionModel(**msg.value)
                yield {
                    "event": "new_alert",
                    "data": alert.to_alert()
                }
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await consumer.stop()

    loop = asyncio.get_event_loop()
    _consumer = AIOKafkaConsumer(
        ALERTS_TOPIC,
        loop=loop,
        bootstrap_servers=[KAFKA_BROKER_URL],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode())
    )

    await _consumer.start()
    return EventSourceResponse(event_generator(_consumer))
