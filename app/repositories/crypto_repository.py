from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_
from .base_repository import BaseRepository
from ..models.crypto import Cryptocurrency, PriceHistory
from ..schemas.crypto_schemas import CryptocurrencyFilter


class CryptocurrencyRepository(BaseRepository[Cryptocurrency]):
    """Репозиторий для работы с криптовалютами"""
    
    def __init__(self):
        super().__init__(Cryptocurrency)
    
    def search_cryptocurrencies(self, filter_params: CryptocurrencyFilter) -> List[Cryptocurrency]:
        """Поиск криптовалют с фильтрацией"""
        db = self._get_db()
        try:
            query = db.query(self.model_class)
            
            if filter_params.search:
                search_term = f"%{filter_params.search.lower()}%"
                query = query.filter(
                    (self.model_class.name.ilike(search_term)) |
                    (self.model_class.symbol.ilike(search_term))
                )
            
            return (query
                   .order_by(self.model_class.market_cap_rank.asc().nulls_last())
                   .offset(filter_params.offset)
                   .limit(filter_params.limit)
                   .all())
        finally:
            db.close()
    
    def find_by_symbol(self, symbol: str) -> Optional[Cryptocurrency]:
        """Поиск криптовалюты по символу"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.symbol.ilike(symbol))
                   .first())
        finally:
            db.close()
    
    def find_top_by_market_cap(self, limit: int = 50) -> List[Cryptocurrency]:
        """Получение топ криптовалют по рыночной капитализации"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.market_cap_rank.isnot(None))
                   .order_by(self.model_class.market_cap_rank.asc())
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def get_cryptocurrencies_with_latest_price(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Получение криптовалют с последними ценами в виде словарей"""
        from ..models.crypto import PriceHistory
        from sqlalchemy import func, desc
        
        db = self._get_db()
        try:
            # Подзапрос для получения последней цены каждой криптовалюты
            latest_price_subquery = (
                db.query(
                    PriceHistory.cryptocurrency_id,
                    func.max(PriceHistory.timestamp).label('max_timestamp')
                )
                .group_by(PriceHistory.cryptocurrency_id)
                .subquery()
            )
            
            # Основной запрос с join последних цен
            query = (
                db.query(
                    self.model_class,
                    PriceHistory.price_usd.label('current_price'),
                    PriceHistory.price_change_percentage_24h,
                    PriceHistory.market_cap,
                    PriceHistory.volume_24h
                )
                .outerjoin(
                    latest_price_subquery,
                    self.model_class.id == latest_price_subquery.c.cryptocurrency_id
                )
                .outerjoin(
                    PriceHistory,
                    (PriceHistory.cryptocurrency_id == self.model_class.id) &
                    (PriceHistory.timestamp == latest_price_subquery.c.max_timestamp)
                )
                .order_by(self.model_class.market_cap_rank.asc().nulls_last())
                .offset(offset)
                .limit(limit)
            )
            
            results = []
            for crypto, current_price, price_change_24h, market_cap, volume_24h in query.all():
                crypto_dict = {
                    'id': crypto.id,
                    'symbol': crypto.symbol,
                    'name': crypto.name,
                    'market_cap_rank': crypto.market_cap_rank,
                    'description': crypto.description,
                    'website': crypto.website,
                    'blockchain': crypto.blockchain,
                    'created_at': crypto.created_at,
                    'updated_at': crypto.updated_at,
                    'current_price': float(current_price) if current_price else None,
                    'price_change_percentage_24h': float(price_change_24h) if price_change_24h else None,
                    'market_cap': float(market_cap) if market_cap else None,
                    'volume_24h': float(volume_24h) if volume_24h else None
                }
                results.append(crypto_dict)
            
            return results
        finally:
            db.close()


