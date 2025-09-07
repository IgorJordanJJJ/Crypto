import clickhouse_connect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator
from .config import settings


class ClickHouseManager:
    def __init__(self):
        self.host = settings.clickhouse_host
        self.port = settings.clickhouse_port
        self.user = settings.clickhouse_user
        self.password = settings.clickhouse_password
        self.database = settings.clickhouse_database
        self._client = None
    
    def get_client(self):
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                database=self.database
            )
        return self._client
    
    def create_database(self):
        client = clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password
        )
        client.command(f"CREATE DATABASE IF NOT EXISTS {self.database}")
    
    def create_tables(self):
        client = self.get_client()
        
        # Create cryptocurrencies table
        client.command("""
        CREATE TABLE IF NOT EXISTS cryptocurrencies (
            id String,
            symbol String,
            name String,
            market_cap_rank Nullable(Int32),
            description Nullable(String),
            website Nullable(String),
            blockchain Nullable(String),
            created_at DateTime,
            updated_at DateTime
        ) ENGINE = MergeTree()
        ORDER BY (id, created_at)
        """)
        
        # Create price_history table
        client.command("""
        CREATE TABLE IF NOT EXISTS price_history (
            id UInt64,
            cryptocurrency_id String,
            timestamp DateTime,
            price_usd Float64,
            volume_24h Nullable(Float64),
            market_cap Nullable(Float64),
            price_change_24h Nullable(Float64),
            price_change_percentage_24h Nullable(Float64)
        ) ENGINE = MergeTree()
        ORDER BY (cryptocurrency_id, timestamp)
        """)
        
        # Create market_data table
        client.command("""
        CREATE TABLE IF NOT EXISTS market_data (
            id UInt64,
            cryptocurrency_id String,
            timestamp DateTime,
            total_supply Nullable(Float64),
            circulating_supply Nullable(Float64),
            max_supply Nullable(Float64),
            ath Nullable(Float64),
            atl Nullable(Float64),
            ath_date Nullable(DateTime),
            atl_date Nullable(DateTime),
            roi_percentage Nullable(Float64)
        ) ENGINE = MergeTree()
        ORDER BY (cryptocurrency_id, timestamp)
        """)
        
        # Create defi_protocols table
        client.command("""
        CREATE TABLE IF NOT EXISTS defi_protocols (
            id String,
            name String,
            category Nullable(String),
            chain Nullable(String),
            tvl Nullable(Float64),
            native_token_id Nullable(String),
            website Nullable(String),
            description Nullable(String),
            created_at DateTime,
            updated_at DateTime
        ) ENGINE = MergeTree()
        ORDER BY (id, created_at)
        """)
        
        # Create tvl_history table
        client.command("""
        CREATE TABLE IF NOT EXISTS tvl_history (
            id UInt64,
            protocol_id String,
            timestamp DateTime,
            tvl Float64,
            tvl_change_24h Nullable(Float64),
            tvl_change_percentage_24h Nullable(Float64)
        ) ENGINE = MergeTree()
        ORDER BY (protocol_id, timestamp)
        """)
    
    def execute_query(self, query: str, parameters: dict = None):
        client = self.get_client()
        return client.query(query, parameters or {})
    
    def insert_data(self, table: str, data: list[dict]):
        client = self.get_client()
        if data:
            client.insert(table, data)


clickhouse_manager = ClickHouseManager()