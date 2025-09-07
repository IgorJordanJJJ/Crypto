from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ClickHouse settings
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "default"
    clickhouse_password: str = "password"
    clickhouse_database: str = "crypto_analytics"
    
    # API settings
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"
    coingecko_api_key: Optional[str] = None
    defipulse_api_url: str = "https://api.defipulse.com"
    defipulse_api_key: Optional[str] = None
    
    # Application settings
    app_name: str = "Crypto DeFi Analyzer"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Batch processing settings
    batch_size: int = 100
    fetch_interval_minutes: int = 15
    max_retries: int = 3
    request_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()