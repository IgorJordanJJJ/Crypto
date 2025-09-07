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
    
    def get_top_gainers(self, limit: int = 10) -> List[PriceHistory]:
        """Получение топ растущих криптовалют за 24ч"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .options(joinedload(self.model_class.cryptocurrency))
                   .filter(self.model_class.timestamp >= one_day_ago)
                   .filter(self.model_class.price_change_percentage_24h > 0)
                   .order_by(desc(self.model_class.price_change_percentage_24h))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_top_losers(self, limit: int = 10) -> List[PriceHistory]:
        """Получение топ падающих криптовалют за 24ч"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .options(joinedload(self.model_class.cryptocurrency))
                   .filter(self.model_class.timestamp >= one_day_ago)
                   .filter(self.model_class.price_change_percentage_24h < 0)
                   .order_by(self.model_class.price_change_percentage_24h.asc())
                   .limit(limit)
                   .all())
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