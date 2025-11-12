from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App Settings
    APP_MODE: str = "webtop_self_contained"
    APP_DATA_DIR: str = "./engine_data"
    APP_LOG_LEVEL: str = "INFO"

    # Exchange Settings
    EXCHANGE_NAME: str = "binance"
    API_KEY: str
    API_SECRET: str
    EXCHANGE_TESTNET: bool = True
    EXCHANGE_PRECISION_REFRESH_SEC: int = 60

    # Execution Pool Settings
    POOL_MAX_OPEN_GROUPS: int = 10
    POOL_COUNT_PYRAMIDS: bool = False

    # Risk Engine Settings
    RISK_LOSS_THRESHOLD_PERCENT: float = -5.0
    RISK_REQUIRE_FULL_PYRAMIDS: bool = True
    RISK_POST_FULL_WAIT_MINUTES: int = 60

    # Database Settings
    DATABASE_URL: str
    POSTGRES_PASSWORD: str

    # Security Settings
    JWT_SECRET: str
    ENCRYPTION_KEY: str
    REDIS_URL: str
    PRECISION_CACHE_EXPIRY_SECONDS: int = 3600

    class Config:
        env_file = BASE_DIR.parent / ".env"
        env_file_encoding = "utf-8"


settings = Settings()