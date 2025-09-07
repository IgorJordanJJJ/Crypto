from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..schemas.defi_schemas import (
    DeFiProtocolResponse,
    DeFiProtocolDetailResponse,
    TVLHistoryResponse,
    DeFiProtocolFilter,
    TVLHistoryFilter
)
from ..repositories.defi_repository import DeFiProtocolRepository
from ..repositories.tvl_history_repository import TVLHistoryRepository
from ..mappers.defi_protocol_mapper import DeFiProtocolMapper
from ..mappers.tvl_history_mapper import TVLHistoryMapper


class DeFiController:
    """Контроллер для работы с DeFi протоколами"""
    
    def __init__(self):
        self.protocol_repo = DeFiProtocolRepository()
        self.tvl_repo = TVLHistoryRepository()
    
    async def get_protocols(
        self,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        category: Optional[str] = Query(None, description="Filter by category"),
        chain: Optional[str] = Query(None, description="Filter by blockchain")
    ) -> List[dict]:
        """Получение списка DeFi протоколов"""
        try:
            filter_params = DeFiProtocolFilter(
                category=category,
                chain=chain,
                limit=limit,
                offset=offset
            )
            
            # Получаем протоколы с последними данными TVL
            protocol_data = self.protocol_repo.get_protocols_with_latest_tvl(
                limit=limit,
                offset=offset
            )
            
            # Применяем фильтры если они заданы
            if category:
                protocol_data = [p for p in protocol_data if p.get('category') == category]
            
            if chain:
                protocol_data = [p for p in protocol_data if p.get('chain') == chain]
            
            return protocol_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_protocol_detail(self, protocol_id: str) -> dict:
        """Получение детальной информации о протоколе"""
        try:
            protocol_data = self.protocol_repo.find_by_id(protocol_id)
            if not protocol_data:
                raise HTTPException(status_code=404, detail="Protocol not found")
            
            return protocol_data
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_tvl_history(
        self,
        protocol_id: str,
        days: int = Query(30, ge=1, le=365)
    ) -> List[dict]:
        """Получение истории TVL протокола"""
        try:
            tvl_data = self.tvl_repo.find_by_protocol_id(protocol_id, days=days)
            return tvl_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_top_protocols_by_tvl(self, limit: int = Query(20, ge=1, le=100)) -> List[dict]:
        """Получение топ протоколов по TVL"""
        try:
            return self.protocol_repo.get_top_by_tvl(limit=limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_categories_summary(self) -> List[dict]:
        """Получение статистики по категориям"""
        try:
            return self.protocol_repo.get_categories_summary()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_chains_summary(self) -> List[dict]:
        """Получение статистики по блокчейнам"""
        try:
            return self.protocol_repo.get_chains_summary()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_tvl_summary(self) -> dict:
        """Получение сводной статистики TVL"""
        try:
            return self.tvl_repo.get_tvl_summary()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_total_tvl_history(self, days: int = Query(30, ge=1, le=365)) -> List[dict]:
        """Получение истории общего TVL"""
        try:
            return self.tvl_repo.get_total_tvl_history(days=days)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_top_tvl_gainers(self, limit: int = Query(10, ge=1, le=50)) -> List[dict]:
        """Получение протоколов с наибольшим ростом TVL"""
        try:
            return self.tvl_repo.get_top_tvl_gainers(limit=limit)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


def create_defi_router() -> APIRouter:
    """Создание роутера для DeFi протоколов"""
    router = APIRouter(prefix="/api/defi", tags=["defi"])
    controller = DeFiController()
    
    @router.get("/protocols")
    async def get_protocols(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        category: Optional[str] = Query(None, description="Filter by category"),
        chain: Optional[str] = Query(None, description="Filter by blockchain")
    ):
        return await controller.get_protocols(limit, offset, category, chain)
    
    @router.get("/protocols/{protocol_id}")
    async def get_protocol_detail(protocol_id: str):
        return await controller.get_protocol_detail(protocol_id)
    
    @router.get("/protocols/{protocol_id}/tvl-history")
    async def get_tvl_history(
        protocol_id: str,
        days: int = Query(30, ge=1, le=365)
    ):
        return await controller.get_tvl_history(protocol_id, days)
    
    @router.get("/top-protocols")
    async def get_top_protocols_by_tvl(limit: int = Query(20, ge=1, le=100)):
        return await controller.get_top_protocols_by_tvl(limit)
    
    @router.get("/categories/summary")
    async def get_categories_summary():
        return await controller.get_categories_summary()
    
    @router.get("/chains/summary")
    async def get_chains_summary():
        return await controller.get_chains_summary()
    
    @router.get("/tvl/summary")
    async def get_tvl_summary():
        return await controller.get_tvl_summary()
    
    @router.get("/tvl/history")
    async def get_total_tvl_history(days: int = Query(30, ge=1, le=365)):
        return await controller.get_total_tvl_history(days)
    
    @router.get("/tvl/top-gainers")
    async def get_top_tvl_gainers(limit: int = Query(10, ge=1, le=50)):
        return await controller.get_top_tvl_gainers(limit)
    
    return router