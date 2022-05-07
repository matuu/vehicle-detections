import asyncio
import json
import logging
import time
from asyncio import AbstractEventLoop

from aiokafka import AIOKafkaProducer, errors, AIOKafkaConsumer

logger = logging.getLogger(__name__)


class KafkaConsumerBuilder:
    def __init__(self, event_loop: AbstractEventLoop, kafka_broker_url: str, topic: str):
        self.event_loop = event_loop
        self.kafka_broker_url = kafka_broker_url
        self.topic = topic

    async def __aenter__(self):
        self._consumer = AIOKafkaConsumer(
            self.topic,
            loop=self.event_loop,
            bootstrap_servers=[self.kafka_broker_url],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            value_deserializer=lambda value: json.loads(value.decode())
        )
        await self._consumer.start()
        return self._consumer

    async def __aexit__(self, exc_type, exc, tb):
        await self._consumer.stop()


class KafkaProducerBuilder:
    def __init__(self, event_loop: AbstractEventLoop, kafka_broker_url: str):
        self.event_loop = event_loop
        self.kafka_broker_url = kafka_broker_url

    async def __aenter__(self):
        self._producer = AIOKafkaProducer(
            loop=self.event_loop,
            bootstrap_servers=[self.kafka_broker_url],
            value_serializer=lambda value: json.dumps(value).encode()
        )
        await self._producer.start()
        return self._producer

    async def __aexit__(self, exc_type, exc, tb):
        await self._producer.stop()


async def waiting_for_broker_startup(
        event_loop: AbstractEventLoop,
        kafka_broker_url: str,
        kafka_timeout: int):
    must_end = time.time() + kafka_timeout
    connected = False
    while time.time() < must_end and not connected:
        try:
            async with KafkaProducerBuilder(event_loop, kafka_broker_url) as producer:
                pass

            logger.info("Connected to kafka broker!")
            connected = True
        except errors.KafkaConnectionError:
            logger.error("Unable to connect to kafka. Waiting...")
            await asyncio.sleep(3)
