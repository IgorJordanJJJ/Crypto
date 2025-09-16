from sqlalchemy import Column, String, Float, DateTime, Integer, Text, Index
from sqlalchemy.sql import func
from .base import Base


class Lab2DataCache(Base):
    """Кэш данных для Лабораторной работы №2"""
    __tablename__ = "lab2_data_cache"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)  # BTC, ETH, etc.
    data_type = Column(String(20), nullable=False)  # "crypto" или "defi"
    interval = Column(String(10), nullable=False)  # "60", "240", "D"
    timestamp = Column(DateTime, nullable=False)  # Время свечи

    # OHLCV данные
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    turnover = Column(Float)

    # Метаданные кэширования
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Индексы для быстрого поиска
    __table_args__ = (
        Index('idx_lab2_symbol_interval_time', 'symbol', 'interval', 'timestamp'),
        Index('idx_lab2_symbol_type', 'symbol', 'data_type'),
        Index('idx_lab2_created_at', 'created_at'),
    )