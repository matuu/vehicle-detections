import asyncio
import logging

from db.session import get_db
from db.models import VehicleDetectionModel
from core.config import settings
from core.kafka import KafkaConsumerBuilder, KafkaProducerBuilder, waiting_for_broker_startup

logger = logging.getLogger(__name__)


async def main_loop(event_loop):
    await waiting_for_broker_startup(
        event_loop,
        settings.KAFKA_BROKER_URL,
        int(settings.KAFKA_TIMEOUT))

    db = get_db()

    async with KafkaConsumerBuilder(event_loop, settings.KAFKA_BROKER_URL, settings.DETECTIONS_TOPIC) as consumer:
        async with KafkaProducerBuilder(event_loop, settings.KAFKA_BROKER_URL) as producer:
            async for msg in consumer:
                vehicle = VehicleDetectionModel(**msg.value)
                if vehicle.category.upper() == settings.SUSPICIOUS_VEHICLE.upper():
                    await producer.send_and_wait(
                        topic=settings.ALERTS_TOPIC,
                        value=vehicle.to_alert()
                    )
                await db.vehicles.insert_one(vehicle.dict())


if __name__ == "__main__":
    logger.info("Starting indexer loop...")
    asyncio.get_event_loop().run_until_complete(main_loop(asyncio.get_event_loop()))
