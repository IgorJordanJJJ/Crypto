from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5435
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_database: str = "crypto_analytics"
    
    # API settings
    bybit_api_url: str = "https://api.bybit.com/v5"
    # Bybit doesn't require API key for public data - it's free
    defillama_api_url: str = "https://api.llama.fi"
    # DefiLlama doesn't require API key - it's free and public
    
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