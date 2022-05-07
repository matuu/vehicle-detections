import asyncio
import logging

from faker import Faker

from vehicle_provider import VehicleProvider
from core.kafka import waiting_for_broker_startup, KafkaProducerBuilder
from core.config import settings

logger = logging.getLogger(__name__)


async def main(event_loop, _faker):
    await waiting_for_broker_startup(
        event_loop,
        settings.KAFKA_BROKER_URL,
        int(settings.KAFKA_TIMEOUT))

    async with KafkaProducerBuilder(event_loop, settings.KAFKA_BROKER_URL) as producer:
        while True:
            detection: dict = _faker.vehicle_object()
            await producer.send_and_wait(settings.DETECTIONS_TOPIC, value=detection)
            logger.info(detection)  # DEBUG
            await asyncio.sleep(1 / settings.DETECTIONS_PER_SECOND)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    _faker = Faker()
    _faker.add_provider(VehicleProvider)

    loop.run_until_complete(main(loop, _faker))
