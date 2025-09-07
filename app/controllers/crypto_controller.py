from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from ..schemas.crypto_schemas import (
    CryptocurrencyResponse,
    CryptocurrencyDetailResponse,
    PriceHistoryResponse,
    MarketDataResponse,
    CryptocurrencyFilter,
    PriceHistoryFilter
)
from ..repositories.crypto_repository import (
    CryptocurrencyRepository,
    PriceHistoryRepository,
    MarketDataRepository
)
from ..mappers.crypto_mapper import CryptocurrencyMapper, PriceHistoryMapper, MarketDataMapper


class CryptocurrencyController:
    """Контроллер для работы с криптовалютами"""
    
    def __init__(self):
        self.crypto_repo = CryptocurrencyRepository()
        self.price_repo = PriceHistoryRepository()
        self.market_repo = MarketDataRepository()
    
    async def get_cryptocurrencies(
        self,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        search: Optional[str] = Query(None, description="Search by name or symbol")
    ) -> List[dict]:
        """Получение списка криптовалют"""
        try:
            filter_params = CryptocurrencyFilter(
                search=search,
                limit=limit,
                offset=offset
            )
            
            # Получаем криптовалюты с последними ценами
            crypto_data = self.crypto_repo.get_cryptocurrencies_with_latest_price(
                limit=limit,
                offset=offset
            )
            
            # Если есть поиск, фильтруем результат
            if search:
                search_lower = search.lower()
                crypto_data = [
                    crypto for crypto in crypto_data
                    if (crypto.get('name', '').lower().find(search_lower) >= 0 or
                        crypto.get('symbol', '').lower().find(search_lower) >= 0)
                ]
            
            return crypto_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_cryptocurrency_detail(self, crypto_id: str) -> dict:
        """Получение детальной информации о криптовалюте"""
        try:
            crypto_data = self.crypto_repo.find_by_id(crypto_id)
            if not crypto_data:
                raise HTTPException(status_code=404, detail="Cryptocurrency not found")
            
            return crypto_data
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_price_history(
        self,
        crypto_id: str,
        days: int = Query(30, ge=1, le=365)
    ) -> List[dict]:
        """Получение истории цен криптовалюты"""
        try:
            price_data = self.price_repo.find_by_crypto_id(crypto_id, days=days)
            return price_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_market_data(
        self,
        crypto_id: str,
        days: int = Query(30, ge=1, le=365)
    ) -> List[dict]:
        """Получение рыночных данных криптовалюты"""
        try:
            market_data = self.market_repo.find_by_crypto_id(crypto_id, days=days)
            return market_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_top_gainers(self, limit: int = Query(10, ge=1, le=50)) -> List[dict]:
        """Получение топ растущих криптовалют"""
        try:
            return self.price_repo.get_top_gainers(limit=limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_top_losers(self, limit: int = Query(10, ge=1, le=50)) -> List[dict]:
        """Получение топ падающих криптовалют"""
        try:
            return self.price_repo.get_top_losers(limit=limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_market_summary(self) -> dict:
        """Получение сводной рыночной статистики"""
        try:
            return self.market_repo.get_market_summary()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


def create_crypto_router() -> APIRouter:
    """Создание роутера для криптовалют"""
    router = APIRouter(prefix="/api/cryptocurrencies", tags=["cryptocurrencies"])
    controller = CryptocurrencyController()
    
    @router.get("")
    async def get_cryptocurrencies(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        search: Optional[str] = Query(None, description="Search by name or symbol")
    ):
        return await controller.get_cryptocurrencies(limit, offset, search)
    
    @router.get("/{crypto_id}")
    async def get_cryptocurrency_detail(crypto_id: str):
        return await controller.get_cryptocurrency_detail(crypto_id)
    
    @router.get("/{crypto_id}/price-history")
    async def get_price_history(
        crypto_id: str,
        days: int = Query(30, ge=1, le=365)
    ):
        return await controller.get_price_history(crypto_id, days)
    
    @router.get("/{crypto_id}/market-data")
    async def get_market_data(
        crypto_id: str,
        days: int = Query(30, ge=1, le=365)
    ):
        return await controller.get_market_data(crypto_id, days)
    
    return router


def create_analytics_router() -> APIRouter:
    """Создание роутера для аналитики"""
    router = APIRouter(prefix="/api/analytics", tags=["analytics"])
    controller = CryptocurrencyController()
    
    @router.get("/top-gainers")
    async def get_top_gainers(limit: int = Query(10, ge=1, le=50)):
        return await controller.get_top_gainers(limit)
    
    @router.get("/top-losers") 
    async def get_top_losers(limit: int = Query(10, ge=1, le=50)):
        return await controller.get_top_losers(limit)
    
    @router.get("/market-summary")
    async def get_market_summary():
        return await controller.get_market_summary()
    
    return router