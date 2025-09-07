from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..services.batch_processor import data_processor
import asyncio
import logging

logger = logging.getLogger(__name__)


class DataController:
    """Контроллер для управления данными"""
    
    async def refresh_data(self, background_tasks: BackgroundTasks) -> dict:
        """Обновление данных из API"""
        try:
            # Запускаем обновление в фоновом режиме
            background_tasks.add_task(self._perform_data_refresh)
            
            return {
                "message": "Data refresh started",
                "status": "in_progress"
            }
            
        except Exception as e:
            logger.error(f"Error starting data refresh: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _perform_data_refresh(self):
        """Выполнение обновления данных"""
        try:
            logger.info("Starting background data refresh")
            await data_processor.run_full_data_processing()
            logger.info("Background data refresh completed")
        except Exception as e:
            logger.error(f"Error in background data refresh: {e}")
    
    async def get_data_status(self) -> dict:
        """Получение статуса данных"""
        try:
            # Импорты внутри метода для избежания циклических зависимостей
            from ..repositories.crypto_repository import CryptocurrencyRepository
            from ..repositories.defi_repository import DeFiProtocolRepository
            
            crypto_repo = CryptocurrencyRepository()
            defi_repo = DeFiProtocolRepository()
            
            crypto_count = crypto_repo.count_all()
            defi_count = defi_repo.count_all()
            
            return {
                "cryptocurrencies_count": crypto_count,
                "defi_protocols_count": defi_count,
                "last_updated": "2024-01-01T00:00:00Z",  # TODO: реализовать реальное время
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Error getting data status: {e}")
            raise HTTPException(status_code=500, detail=str(e))


def create_data_router() -> APIRouter:
    """Создание роутера для управления данными"""
    router = APIRouter(prefix="/api/data", tags=["data"])
    controller = DataController()
    
    @router.post("/refresh")
    async def refresh_data(background_tasks: BackgroundTasks):
        return await controller.refresh_data(background_tasks)
    
    @router.get("/status")
    async def get_data_status():
        return await controller.get_data_status()
    
    return router