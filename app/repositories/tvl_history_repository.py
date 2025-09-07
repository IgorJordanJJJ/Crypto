from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, func, and_
from sqlalchemy.orm import joinedload
from .base_repository import BaseRepository
from ..models.crypto import TVLHistory, DeFiProtocol


class TVLHistoryRepository(BaseRepository[TVLHistory]):
    """Репозиторий для работы с историей TVL"""
    
    def __init__(self):
        super().__init__(TVLHistory)
    
    def find_by_protocol_id(self, protocol_id: str, days: int = 30, limit: int = 1000) -> List[TVLHistory]:
        """Получение истории TVL для протокола"""
        start_date = datetime.utcnow() - timedelta(days=days)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.protocol_id == protocol_id)
                   .filter(self.model_class.timestamp >= start_date)
                   .order_by(desc(self.model_class.timestamp))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_total_tvl_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получение истории общего TVL по дням"""
        start_date = datetime.utcnow() - timedelta(days=days)
        db = self._get_db()
        try:
            result = (db.query(
                        func.date(self.model_class.timestamp).label('date'),
                        func.sum(self.model_class.tvl).label('total_tvl'),
                        func.count(func.distinct(self.model_class.protocol_id)).label('protocols_count')
                      )
                     .filter(self.model_class.timestamp >= start_date)
                     .group_by(func.date(self.model_class.timestamp))
                     .order_by(desc(func.date(self.model_class.timestamp)))
                     .all())
            
            return [
                {
                    'date': str(r.date),
                    'total_tvl': float(r.total_tvl or 0),
                    'protocols_count': r.protocols_count
                }
                for r in result
            ]
        finally:
            db.close()
    
    def get_tvl_changes_24h(self) -> List[TVLHistory]:
        """Получение изменений TVL за 24ч для всех протоколов"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .options(joinedload(self.model_class.protocol))
                   .filter(self.model_class.timestamp >= one_day_ago)
                   .filter(self.model_class.tvl_change_percentage_24h.isnot(None))
                   .order_by(desc(self.model_class.tvl_change_percentage_24h))
                   .all())
        finally:
            db.close()
    
    def get_top_tvl_gainers(self, limit: int = 10) -> List[TVLHistory]:
        """Получение протоколов с наибольшим ростом TVL за 24ч"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .options(joinedload(self.model_class.protocol))
                   .filter(self.model_class.timestamp >= one_day_ago)
                   .filter(self.model_class.tvl_change_percentage_24h > 0)
                   .order_by(desc(self.model_class.tvl_change_percentage_24h))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_tvl_summary(self) -> Dict[str, Any]:
        """Получение сводной статистики TVL"""
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        db = self._get_db()
        try:
            result = (db.query(
                        func.sum(self.model_class.tvl).label('total_tvl'),
                        func.count(func.distinct(self.model_class.protocol_id)).label('total_protocols'),
                        func.avg(self.model_class.tvl).label('avg_tvl'),
                        func.max(self.model_class.tvl).label('max_tvl'),
                        func.min(self.model_class.tvl).label('min_tvl')
                      )
                     .filter(self.model_class.timestamp >= one_day_ago)
                     .first())
            
            if result:
                return {
                    'total_tvl': float(result.total_tvl or 0),
                    'total_protocols': result.total_protocols or 0,
                    'avg_tvl': float(result.avg_tvl or 0),
                    'max_tvl': float(result.max_tvl or 0),
                    'min_tvl': float(result.min_tvl or 0)
                }
            return {
                'total_tvl': 0,
                'total_protocols': 0,
                'avg_tvl': 0,
                'max_tvl': 0,
                'min_tvl': 0
            }
        finally:
            db.close()