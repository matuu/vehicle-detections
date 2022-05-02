import os
import logging
import json
import time

from kafka import KafkaProducer, errors
from faker import Faker

from vehicle_provider import VehicleProvider


logger = logging.getLogger(__name__)

KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
DETECTIONS_TOPIC = os.environ.get("DETECTIONS_TOPIC")
DETECTIONS_PER_SECOND = float(os.environ.get("DETECTIONS_PER_SECOND"))
SLEEP_TIME = 1 / DETECTIONS_PER_SECOND
KAFKA_TIMEOUT = os.environ.get("KAFKA_TIMEOUT", 120)

fake = Faker()
fake.add_provider(VehicleProvider)


def build_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER_URL],
            # Encode all values as JSON
            value_serializer=lambda value: json.dumps(value).encode(),
        )
    except errors.NoBrokersAvailable:
        return


if __name__ == "__main__":

    must_end = time.time() + KAFKA_TIMEOUT
    logger.info("waiting for kafka broker...")
    while (producer := build_producer()) is None and time.time() < must_end:
        # waiting for kafka broker services
        time.sleep(1)

    if producer is None:
        logger.info("Timeout waiting for kafka broker. Exit!")
        exit(1)

    logger.info("kafka connected!")
    while True:
        detection: dict = fake.vehicle_object()
        producer.send(DETECTIONS_TOPIC, value=detection)
        logger.info(detection)  # DEBUG
        time.sleep(SLEEP_TIME)

    producer.flush()
