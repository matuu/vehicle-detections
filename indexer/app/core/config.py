import os


class Settings:
    PROJECT_NAME: str = "VehicleDetection"

    KAFKA_BROKER_URL: str = os.getenv("KAFKA_BROKER_URL")
    DETECTIONS_TOPIC: str = os.environ.get("DETECTIONS_TOPIC")
    ALERTS_TOPIC: str = os.getenv("ALERTS_TOPIC")
    SUSPICIOUS_VEHICLE = os.environ.get("SUSPICIOUS_VEHICLE")
    KAFKA_TIMEOUT = int(os.getenv("KAFKA_TIMEOUT", 120))

    MONGO_INITDB_ROOT_USERNAME: str = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    MONGO_INITDB_ROOT_PASSWORD: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongo")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))


settings = Settings()
