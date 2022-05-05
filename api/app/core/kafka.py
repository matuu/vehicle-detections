import asyncio
import json
import logging
import time
from asyncio import AbstractEventLoop

from aiokafka import AIOKafkaConsumer, errors


logger = logging.getLogger(__name__)


class KafkaConsumerBuilder:
    def __init__(self, event_loop: AbstractEventLoop, kafka_broker_url: str, topic: str):
        self.event_loop = event_loop
        self.kafka_broker_url = kafka_broker_url
        self.topic = topic

    def __call__(self):
        _consumer = AIOKafkaConsumer(
            self.topic,
            loop=self.event_loop,
            bootstrap_servers=[self.kafka_broker_url],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode())
        )
        await _consumer.start()
        yield _consumer
        await _consumer.stop()


async def waiting_for_broker_startup(
        event_loop: AbstractEventLoop,
        alert_topic: str,
        kafka_broker_url: str,
        kafka_timeout: int):
    must_end = time.time() + kafka_timeout
    connected = False
    while time.time() < must_end and not connected:
        try:
            _consumer = AIOKafkaConsumer(
                alert_topic,
                loop=event_loop,
                bootstrap_servers=[kafka_broker_url],
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda value: json.loads(value.decode())
            )
            await _consumer.start()
            await _consumer.stop()
            logger.info("Connected to kafka broker!")
            connected = True
        except errors.KafkaConnectionError:
            logger.error("Unable to connect to kafka. Waiting...")
            await asyncio.sleep(1)
