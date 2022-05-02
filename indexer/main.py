import asyncio
import json
import logging
import os
import time
from kafka import KafkaConsumer, KafkaProducer, errors

from db import db
from models import VehicleDetectionModel


logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
DETECTIONS_TOPIC = os.environ.get("DETECTIONS_TOPIC")
ALERTS_TOPIC = os.environ.get("ALERTS_TOPIC")
SUSPICIOUS_VEHICLE = os.environ.get("SUSPICIOUS_VEHICLE")
KAFKA_TIMEOUT = os.environ.get("KAFKA_TIMEOUT", 120)


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


def build_alert_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER_URL],
            # Encode all values as JSON
            value_serializer=lambda value: value.json().encode(),
        )
    except errors.NoBrokersAvailable:
        return


async def main_loop():

    while (message := next(consumer)) is not None:
        vehicle = VehicleDetectionModel(**message.value)
        if vehicle.category.upper() == SUSPICIOUS_VEHICLE.upper():
            alert_producer.send(ALERTS_TOPIC, value=vehicle)
        await db.vehicles.insert_one(vehicle.dict())


if __name__ == "__main__":

    must_end = time.time() + KAFKA_TIMEOUT
    logger.info("waiting for kafka broker...")
    while (consumer := build_consumer()) is None and time.time() < must_end:
        # waiting for kafka broker services
        time.sleep(1)

    if consumer is None:
        logger.info("Timeout waiting for kafka broker. Exit!")
        exit(1)

    logger.info("kafka connected!")
    alert_producer = build_alert_producer()
    logger.info("Starting indexer loop...")
    asyncio.get_event_loop().run_until_complete(main_loop())
