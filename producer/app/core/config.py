import os


class Settings:
    PROJECT_NAME: str = "VehicleDetection"

    KAFKA_BROKER_URL: str = os.getenv("KAFKA_BROKER_URL")
    DETECTIONS_TOPIC: str = os.environ.get("DETECTIONS_TOPIC")
    DETECTIONS_PER_SECOND: float = float(os.environ.get("DETECTIONS_PER_SECOND"))
    ALERTS_TOPIC: str = os.getenv("ALERTS_TOPIC")

    KAFKA_TIMEOUT = int(os.getenv("KAFKA_TIMEOUT", 120))
    ALERT_GROUP = os.getenv("ALERT_GROUP", "alerts")
    
    MONGO_INITDB_ROOT_USERNAME: str = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    MONGO_INITDB_ROOT_PASSWORD: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongo")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))


settings = Settings()
