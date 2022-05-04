"""
API of vehicle detections solution
"""
import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Optional

from aiokafka import AIOKafkaConsumer
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sse_starlette.sse import EventSourceResponse


from auth import User, Token, authenticate_user, create_access_token, TokenData, get_user, get_current_active_user
from models import VehicleDetectionModel
from db import db


PROJECT_NAME = "VehicleDetection"
KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
ALERTS_TOPIC = os.environ.get("ALERTS_TOPIC")
KAFKA_TIMEOUT = int(os.environ.get("KAFKA_TIMEOUT", 120))
ALERT_GROUP = os.environ.get("ALERT_GROUP", "alerts")
ACCESS_TOKEN_EXPIRE_MINUTES = 30


app = FastAPI(title=PROJECT_NAME)


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


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
async def detections(token: str = Depends(get_current_active_user), skip: int = 0, limit: int = 100):
    data = await db["vehicles"].find().skip(skip).to_list(limit)
    return data


@app.get(
    "/stats",
    response_description="Stats about vehicle detections group by Make field"
)
async def stats(token: str = Depends(get_current_active_user)):
    cursor = db["vehicles"].aggregate(
        [{
            "$group": {
                "_id": "$make",
                "count": {"$sum": 1}
            }
        }]
    )
    stats_data = list()

    async for doc in cursor:
        stats_data.append((doc['_id'], doc['count']))
    return dict(sorted(stats_data))


@app.get('/alerts')
async def alerts_stream(request: Request, token: str = Depends(get_current_active_user)):

    async def event_generator():
        try:
            # Consume messages
            async for msg in _consumer:
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
            await _consumer.stop()

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
    return EventSourceResponse(event_generator())
