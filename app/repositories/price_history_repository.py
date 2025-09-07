from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, and_
from sqlalchemy.orm import joinedload
from .base_repository import BaseRepository
from ..models.crypto import PriceHistory, Cryptocurrency


class PriceHistoryRepository(BaseRepository[PriceHistory]):
    """Репозиторий для работы с историей цен"""
    
    def __init__(self):
        super().__init__(PriceHistory)
    
    def find_by_crypto_id(self, crypto_id: str, days: int = 30, limit: int = 1000) -> List[PriceHistory]:
        """Получение истории цен для криптовалюты"""
        start_date = datetime.utcnow() - timedelta(days=days)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.cryptocurrency_id == crypto_id)
                   .filter(self.model_class.timestamp >= start_date)
                   .order_by(desc(self.model_class.timestamp))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_latest_prices(self, limit: int = 100) -> List[PriceHistory]:
        """Получение последних цен для всех криптовалют"""
        db = self._get_db()
        try:
            # Подзапрос для получения последних временных меток для каждой криптовалюты
            subquery = (db.query(self.model_class.cryptocurrency_id,
                               db.func.max(self.model_class.timestamp).label('max_timestamp'))
                        .group_by(self.model_class.cryptocurrency_id)
                        .subquery())
            
            return (db.query(self.model_class)
                   .options(joinedload(self.model_class.cryptocurrency))
                   .join(subquery, 
                        and_(self.model_class.cryptocurrency_id == subquery.c.cryptocurrency_id,
                             self.model_class.timestamp == subquery.c.max_timestamp))
                   .order_by(desc(self.model_class.timestamp))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_top_gainers(self, limit: int = 10) -> List[dict]:
        """Получение топ растущих криптовалют за 24ч"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            results = (db.query(self.model_class)
                      .options(joinedload(self.model_class.cryptocurrency))
                      .filter(self.model_class.timestamp >= one_day_ago)
                      .filter(self.model_class.price_change_percentage_24h > 0)
                      .order_by(desc(self.model_class.price_change_percentage_24h))
                      .limit(limit)
                      .all())
            
            # Конвертируем в словари для JSON сериализации
            gainers = []
            for price_record in results:
                gainers.append({
                    'id': price_record.cryptocurrency.id if price_record.cryptocurrency else price_record.cryptocurrency_id,
                    'symbol': price_record.cryptocurrency.symbol if price_record.cryptocurrency else 'Unknown',
                    'name': price_record.cryptocurrency.name if price_record.cryptocurrency else 'Unknown',
                    'current_price': float(price_record.price_usd) if price_record.price_usd else 0,
                    'price_change_percentage_24h': float(price_record.price_change_percentage_24h) if price_record.price_change_percentage_24h else 0,
                    'volume_24h': float(price_record.volume_24h) if price_record.volume_24h else 0,
                    'market_cap': float(price_record.market_cap) if price_record.market_cap else 0,
                    'timestamp': price_record.timestamp
                })
            
            return gainers
        finally:
            db.close()
    
    def get_top_losers(self, limit: int = 10) -> List[dict]:
        """Получение топ падающих криптовалют за 24ч"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            results = (db.query(self.model_class)
                      .options(joinedload(self.model_class.cryptocurrency))
                      .filter(self.model_class.timestamp >= one_day_ago)
                      .filter(self.model_class.price_change_percentage_24h < 0)
                      .order_by(self.model_class.price_change_percentage_24h.asc())
                      .limit(limit)
                      .all())
            
            # Конвертируем в словари для JSON сериализации
            losers = []
            for price_record in results:
                losers.append({
                    'id': price_record.cryptocurrency.id if price_record.cryptocurrency else price_record.cryptocurrency_id,
                    'symbol': price_record.cryptocurrency.symbol if price_record.cryptocurrency else 'Unknown',
                    'name': price_record.cryptocurrency.name if price_record.cryptocurrency else 'Unknown',
                    'current_price': float(price_record.price_usd) if price_record.price_usd else 0,
                    'price_change_percentage_24h': float(price_record.price_change_percentage_24h) if price_record.price_change_percentage_24h else 0,
                    'volume_24h': float(price_record.volume_24h) if price_record.volume_24h else 0,
                    'market_cap': float(price_record.market_cap) if price_record.market_cap else 0,
                    'timestamp': price_record.timestamp
                })
            
            return losers
        finally:
            db.close()

    def get_price_chart_data(self, crypto_id: str, days: int = 30) -> List[PriceHistory]:
        """Получение данных для графика цены"""
        start_date = datetime.utcnow() - timedelta(days=days)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.cryptocurrency_id == crypto_id)
                   .filter(self.model_class.timestamp >= start_date)
                   .order_by(self.model_class.timestamp.asc())
                   .all())
        finally:
            db.close()