"""
API of vehicle detections solution
"""
import asyncio
import json
import logging
from datetime import timedelta
from typing import List

from aiokafka import AIOKafkaConsumer
from fastapi import Depends, FastAPI, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
from app.auth import Token, authenticate_user, get_current_active_user, exists_username, create_user
from app.core.security import create_access_token
from app.core.utils import waiting_for_broker_startup
from app.db.models import VehicleDetectionModel, UserCreationModel, BaseUserModel
from app.db.session import get_db

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.PROJECT_NAME)


@app.on_event("startup")
async def startup_event():
    """We try to connect to kafka broker, before to start up api server"""
    loop = asyncio.get_event_loop()
    await waiting_for_broker_startup(loop, settings.ALERTS_TOPIC, settings.KAFKA_BROKER_URL, settings.KAFKA_TIMEOUT)


@app.post("/token", response_model=Token)
async def login_for_access_token(db=Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(db.users, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=BaseUserModel)
async def user_creation(db=Depends(get_db), new_user: UserCreationModel = Body(...)):
    if await exists_username(db.users, new_user.username):
        raise HTTPException(
            status_code=409,
            detail=f"User with username {new_user.username} already exist."
        )
    user = jsonable_encoder(new_user)
    _user = await create_user(db.users, user)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=_user.dict(exclude={'id'}))


@app.get("/users/me/", response_model=BaseUserModel)
async def read_users_me(current_user: BaseUserModel = Depends(get_current_active_user)):
    return current_user.dict()


@app.get(
    "/detections",
    response_description="List all vehicles detections",
    response_model=List[VehicleDetectionModel]
)
async def detections(
        token: str = Depends(get_current_active_user),
        db=Depends(get_db),
        skip: int = 0,
        limit: int = 100):
    data = await db.vehicles.find().skip(skip).to_list(limit)
    return data


@app.get(
    "/stats",
    response_description="Stats about vehicle detections group by Make field"
)
async def stats(token: str = Depends(get_current_active_user), db=Depends(get_db)):
    cursor = db.vehicles.aggregate(
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
            await _consumer.stop()

    loop = asyncio.get_event_loop()
    _consumer = AIOKafkaConsumer(
        settings.ALERTS_TOPIC,
        loop=loop,
        bootstrap_servers=[settings.KAFKA_BROKER_URL],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode())
    )

    await _consumer.start()
    return EventSourceResponse(event_generator())
