from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from .base_repository import BaseRepository
from ..models import MarketData, PriceHistory


class MarketDataRepository(BaseRepository[MarketData]):
    """Репозиторий для работы с рыночными данными"""
    
    def __init__(self):
        super().__init__(MarketData)
    
    def find_by_crypto_id(self, crypto_id: str, days: int = 30, limit: int = 1000) -> List[MarketData]:
        """Получение рыночных данных для криптовалюты"""
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
    
    def get_latest_market_data(self, crypto_id: str) -> Optional[MarketData]:
        """Получение последних рыночных данных для криптовалюты"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.cryptocurrency_id == crypto_id)
                   .order_by(desc(self.model_class.timestamp))
                   .first())
        finally:
            db.close()

    def get_market_summary(self) -> Dict[str, Any]:
        """Получение сводной рыночной статистики"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            result = (db.query(
                        func.count(func.distinct(self.model_class.cryptocurrency_id)).label('total_assets'),
                        func.avg(self.model_class.roi_percentage).label('avg_roi')
                      )
                     .filter(self.model_class.timestamp >= one_day_ago)
                     .first())
            
            if result:
                return {
                    'total_assets': result.total_assets or 0,
                    'avg_roi': float(result.avg_roi or 0)
                }
            return {'total_assets': 0, 'avg_roi': 0}
        finally:
            db.close()