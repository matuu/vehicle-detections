import os


class Settings:
    PROJECT_NAME: str = "VehicleDetection"

    KAFKA_BROKER_URL: str = os.getenv("KAFKA_BROKER_URL")
    ALERTS_TOPIC = os.getenv("ALERTS_TOPIC")
    KAFKA_TIMEOUT = int(os.getenv("KAFKA_TIMEOUT", 120))
    ALERT_GROUP = os.getenv("ALERT_GROUP", "alerts")
    
    MONGO_INITDB_ROOT_USERNAME: str = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    MONGO_INITDB_ROOT_PASSWORD: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    MONGO_HOST: str = os.getenv("MONGO_HOST", "mongo")
    MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))
    
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # in mins


settings = Settings()
