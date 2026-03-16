import os

class Settings:
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis") # Default to 'redis' for Docker
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

settings = Settings()