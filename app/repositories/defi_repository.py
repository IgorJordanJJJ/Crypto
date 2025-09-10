from typing import List, Optional, Dict, Any
from sqlalchemy import desc, func
from sqlalchemy.orm import joinedload
from .base_repository import BaseRepository
from ..models import DeFiProtocol, TVLHistory
from ..schemas.defi_schemas import DeFiProtocolFilter


class DeFiProtocolRepository(BaseRepository[DeFiProtocol]):
    """Репозиторий для работы с DeFi протоколами"""
    
    def __init__(self):
        super().__init__(DeFiProtocol)
    
    def search_protocols(self, filter_params: DeFiProtocolFilter) -> List[DeFiProtocol]:
        """Поиск DeFi протоколов с фильтрацией"""
        db = self._get_db()
        try:
            query = db.query(self.model_class)
            
            if filter_params.category:
                query = query.filter(self.model_class.category == filter_params.category)
            
            if filter_params.chain:
                query = query.filter(self.model_class.chain == filter_params.chain)
            
            return (query
                   .order_by(desc(self.model_class.tvl))
                   .offset(filter_params.offset)
                   .limit(filter_params.limit)
                   .all())
        finally:
            db.close()
    
    def find_by_category(self, category: str, limit: int = 50) -> List[DeFiProtocol]:
        """Поиск протоколов по категории"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.category == category)
                   .order_by(desc(self.model_class.tvl))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def find_by_chain(self, chain: str, limit: int = 50) -> List[DeFiProtocol]:
        """Поиск протоколов по блокчейну"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.chain == chain)
                   .order_by(desc(self.model_class.tvl))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_top_by_tvl(self, limit: int = 20) -> List[DeFiProtocol]:
        """Получение топ протоколов по TVL"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.tvl > 0)
                   .order_by(desc(self.model_class.tvl))
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_protocols_with_latest_tvl(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Получение протоколов с последними данными TVL в виде словарей"""
        from ..models import TVLHistory
        from sqlalchemy import func
        
        db = self._get_db()
        try:
            # Подзапрос для получения последней записи TVL каждого протокола
            latest_tvl_subquery = (
                db.query(
                    TVLHistory.protocol_id,
                    func.max(TVLHistory.timestamp).label('max_timestamp')
                )
                .group_by(TVLHistory.protocol_id)
                .subquery()
            )
            
            # Основной запрос с join последних TVL данных
            query = (
                db.query(
                    self.model_class,
                    TVLHistory.tvl_change_24h,
                    TVLHistory.tvl_change_percentage_24h
                )
                .outerjoin(
                    latest_tvl_subquery,
                    self.model_class.id == latest_tvl_subquery.c.protocol_id
                )
                .outerjoin(
                    TVLHistory,
                    (TVLHistory.protocol_id == self.model_class.id) &
                    (TVLHistory.timestamp == latest_tvl_subquery.c.max_timestamp)
                )
                .order_by(desc(self.model_class.tvl))
                .offset(offset)
                .limit(limit)
            )
            
            results = []
            for protocol, tvl_change_24h, tvl_change_percentage_24h in query.all():
                protocol_dict = {
                    'id': protocol.id,
                    'name': protocol.name,
                    'category': protocol.category,
                    'chain': protocol.chain,
                    'tvl': float(protocol.tvl) if protocol.tvl else 0,
                    'native_token_id': protocol.native_token_id,
                    'website': protocol.website,
                    'description': protocol.description,
                    'created_at': protocol.created_at,
                    'updated_at': protocol.updated_at,
                    'tvl_change_24h': float(tvl_change_24h) if tvl_change_24h else None,
                    'tvl_change_percentage_24h': float(tvl_change_percentage_24h) if tvl_change_percentage_24h else None
                }
                results.append(protocol_dict)
            
            return results
        finally:
            db.close()
    
    def get_categories_summary(self) -> List[Dict[str, Any]]:
        """Получение сводной статистики по категориям"""
        db = self._get_db()
        try:
            result = (db.query(
                        self.model_class.category,
                        func.count().label('protocols_count'),
                        func.sum(self.model_class.tvl).label('total_tvl'),
                        func.avg(self.model_class.tvl).label('avg_tvl'),
                        func.max(self.model_class.tvl).label('max_tvl')
                      )
                     .filter(self.model_class.tvl > 0)
                     .group_by(self.model_class.category)
                     .order_by(desc(func.sum(self.model_class.tvl)))
                     .all())
            
            return [
                {
                    'category': r.category,
                    'protocols_count': r.protocols_count,
                    'total_tvl': float(r.total_tvl or 0),
                    'avg_tvl': float(r.avg_tvl or 0),
                    'max_tvl': float(r.max_tvl or 0)
                }
                for r in result
            ]
        finally:
            db.close()
    
    def get_chains_summary(self) -> List[Dict[str, Any]]:
        """Получение сводной статистики по блокчейнам"""
        db = self._get_db()
        try:
            result = (db.query(
                        self.model_class.chain,
                        func.count().label('protocols_count'),
                        func.sum(self.model_class.tvl).label('total_tvl'),
                        func.avg(self.model_class.tvl).label('avg_tvl'),
                        func.max(self.model_class.tvl).label('max_tvl')
                      )
                     .filter(self.model_class.tvl > 0)
                     .group_by(self.model_class.chain)
                     .order_by(desc(func.sum(self.model_class.tvl)))
                     .all())
            
            return [
                {
                    'chain': r.chain,
                    'protocols_count': r.protocols_count,
                    'total_tvl': float(r.total_tvl or 0),
                    'avg_tvl': float(r.avg_tvl or 0),
                    'max_tvl': float(r.max_tvl or 0)
                }
                for r in result
            ]
        finally:
            db.close()