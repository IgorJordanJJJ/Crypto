from fastapi import APIRouter, HTTPException, BackgroundTasks
from ..services.batch_processor import data_processor
from ..services.data_fetcher import BybitFetcher, DefiLlamaFetcher, YFinanceFetcher
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
    
    # =================================
    # НОВЫЕ МЕТОДЫ ДЛЯ РУЧНОГО ТЕСТИРОВАНИЯ
    # =================================
    
    async def test_bybit_connection(self) -> dict:
        """Тестирование подключения к Bybit API"""
        try:
            logger.info("Testing Bybit API connection...")
            
            async with BybitFetcher() as fetcher:
                # Получаем несколько тикеров для теста
                tickers = await fetcher.fetch_ticker_24hr(category="spot")
                
                if tickers:
                    # Берем первые 5 для демонстрации
                    sample_data = tickers[:5]
                    return {
                        "status": "success",
                        "message": "Bybit API connection successful",
                        "total_symbols": len(tickers),
                        "sample_data": sample_data
                    }
                else:
                    return {
                        "status": "error", 
                        "message": "No data received from Bybit API"
                    }
                    
        except Exception as e:
            logger.error(f"Bybit API test failed: {e}")
            return {
                "status": "error",
                "message": f"Bybit API test failed: {str(e)}"
            }
    
    async def test_defillama_connection(self) -> dict:
        """Тестирование подключения к DefiLlama API"""
        try:
            logger.info("Testing DefiLlama API connection...")
            
            async with DefiLlamaFetcher() as fetcher:
                # Получаем протоколы для теста
                protocols = await fetcher.fetch_protocols()
                
                if protocols:
                    # Берем топ-5 по TVL для демонстрации, обрабатываем None значения
                    sample_data = sorted(protocols, key=lambda x: x.get('tvl') or 0, reverse=True)[:5]
                    return {
                        "status": "success",
                        "message": "DefiLlama API connection successful", 
                        "total_protocols": len(protocols),
                        "sample_data": sample_data
                    }
                else:
                    return {
                        "status": "error",
                        "message": "No data received from DefiLlama API"
                    }
                    
        except Exception as e:
            logger.error(f"DefiLlama API test failed: {e}")
            return {
                "status": "error",
                "message": f"DefiLlama API test failed: {str(e)}"
            }
    
    async def test_yfinance_connection(self) -> dict:
        """Тестирование подключения к YFinance API"""
        try:
            logger.info("Testing YFinance API connection...")
            
            async with YFinanceFetcher() as fetcher:
                # Получаем данные по топ криптовалютам для теста
                crypto_data = await fetcher.fetch_crypto_data(["BTC-USD", "ETH-USD", "ADA-USD"])
                
                if crypto_data:
                    return {
                        "status": "success",
                        "message": "YFinance API connection successful",
                        "total_cryptos": len(crypto_data),
                        "sample_data": crypto_data
                    }
                else:
                    return {
                        "status": "error", 
                        "message": "No data received from YFinance API"
                    }
                    
        except Exception as e:
            logger.error(f"YFinance API test failed: {e}")
            return {
                "status": "error",
                "message": f"YFinance API test failed: {str(e)}"
            }
    
    async def fetch_crypto_data_manual(self, background_tasks: BackgroundTasks) -> dict:
        """Ручной запуск процесса получения данных о криптовалютах"""
        try:
            background_tasks.add_task(self._fetch_crypto_data_background)
            
            return {
                "message": "Crypto data fetch started manually",
                "status": "in_progress",
                "process": "cryptocurrency_data"
            }
            
        except Exception as e:
            logger.error(f"Error starting manual crypto data fetch: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _fetch_crypto_data_background(self):
        """Фоновый процесс получения данных о криптовалютах"""
        try:
            logger.info("Starting manual crypto data fetch...")
            await data_processor.process_cryptocurrency_data()
            logger.info("Manual crypto data fetch completed")
        except Exception as e:
            logger.error(f"Error in manual crypto data fetch: {e}")
    
    async def fetch_defi_data_manual(self, background_tasks: BackgroundTasks) -> dict:
        """Ручной запуск процесса получения DeFi данных"""
        try:
            background_tasks.add_task(self._fetch_defi_data_background)
            
            return {
                "message": "DeFi data fetch started manually", 
                "status": "in_progress",
                "process": "defi_data"
            }
            
        except Exception as e:
            logger.error(f"Error starting manual DeFi data fetch: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _fetch_defi_data_background(self):
        """Фоновый процесс получения DeFi данных"""
        try:
            logger.info("Starting manual DeFi data fetch...")
            await data_processor.process_defi_data()
            logger.info("Manual DeFi data fetch completed")
        except Exception as e:
            logger.error(f"Error in manual DeFi data fetch: {e}")
    
    async def get_sample_crypto_data(self, limit: int = 10) -> dict:
        """Получение примера данных из Bybit (без сохранения в БД)"""
        try:
            logger.info(f"Fetching sample crypto data (limit: {limit})...")
            
            async with BybitFetcher() as fetcher:
                spot_data = await fetcher.fetch_spot_symbols()
                
                if spot_data:
                    sample = spot_data[:limit]
                    return {
                        "status": "success",
                        "total_available": len(spot_data),
                        "sample_size": len(sample),
                        "data": sample,
                        "note": "This is sample data, not saved to database"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "No crypto data available"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting sample crypto data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_sample_yfinance_data(self, limit: int = 10) -> dict:
        """Получение примера данных из YFinance (без сохранения в БД)"""
        try:
            logger.info(f"Fetching sample YFinance data (limit: {limit})...")
            
            async with YFinanceFetcher() as fetcher:
                # Ограничиваем список символов
                symbols = fetcher.crypto_symbols[:limit]
                yfinance_data = await fetcher.fetch_crypto_data(symbols)
                
                if yfinance_data:
                    return {
                        "status": "success",
                        "total_available": len(fetcher.crypto_symbols),
                        "sample_size": len(yfinance_data),
                        "data": yfinance_data,
                        "note": "This is sample data from Yahoo Finance, not saved to database"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "No YFinance data available"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting sample crypto data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_sample_defi_data(self, limit: int = 10) -> dict:
        """Получение примера DeFi данных из DefiLlama (без сохранения в БД)"""
        try:
            logger.info(f"Fetching sample DeFi data (limit: {limit})...")
            
            async with DefiLlamaFetcher() as fetcher:
                protocols = await fetcher.fetch_protocols()
                
                if protocols:
                    # Сортируем по TVL и берем топ, обрабатываем None значения
                    sorted_protocols = sorted(protocols, key=lambda x: x.get('tvl') or 0, reverse=True)
                    sample = sorted_protocols[:limit]
                    
                    return {
                        "status": "success", 
                        "total_available": len(protocols),
                        "sample_size": len(sample),
                        "data": sample,
                        "note": "This is sample data, not saved to database"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "No DeFi data available"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting sample DeFi data: {e}")
            raise HTTPException(status_code=500, detail=str(e))


def create_data_router() -> APIRouter:
    """Создание роутера для управления данными"""
    router = APIRouter(prefix="/api/data", tags=["data"])
    controller = DataController()
    
    # ========================================
    # ОСНОВНЫЕ ЭНДПОИНТЫ (существующие)
    # ========================================
    
    @router.post("/refresh")
    async def refresh_data(background_tasks: BackgroundTasks):
        """Полное обновление всех данных (crypto + DeFi)"""
        return await controller.refresh_data(background_tasks)
    
    @router.get("/status")
    async def get_data_status():
        """Статус данных в базе"""
        return await controller.get_data_status()
    
    # ========================================
    # НОВЫЕ ЭНДПОИНТЫ ДЛЯ РУЧНОГО УПРАВЛЕНИЯ
    # ========================================
    
    # Тестирование API подключений
    @router.get("/test/bybit")
    async def test_bybit_api():
        """🔍 Тест подключения к Bybit API"""
        return await controller.test_bybit_connection()
    
    @router.get("/test/defillama") 
    async def test_defillama_api():
        """🔍 Тест подключения к DefiLlama API"""
        return await controller.test_defillama_connection()
    
    @router.get("/test/yfinance")
    async def test_yfinance_api():
        """🔍 Тест подключения к YFinance API"""
        return await controller.test_yfinance_connection()
    
    # Ручной запуск процессов (с сохранением в БД)
    @router.post("/fetch/crypto")
    async def fetch_crypto_data_manual(background_tasks: BackgroundTasks):
        """🚀 Ручной запуск получения данных криптовалют"""
        return await controller.fetch_crypto_data_manual(background_tasks)
    
    @router.post("/fetch/defi")
    async def fetch_defi_data_manual(background_tasks: BackgroundTasks):
        """🚀 Ручной запуск получения DeFi данных"""
        return await controller.fetch_defi_data_manual(background_tasks)
    
    # Получение примеров данных (БЕЗ сохранения в БД)
    @router.get("/sample/crypto")
    async def get_sample_crypto_data(limit: int = 10):
        """👀 Получить пример данных из Bybit (только просмотр)"""
        return await controller.get_sample_crypto_data(limit)
    
    @router.get("/sample/defi") 
    async def get_sample_defi_data(limit: int = 10):
        """👀 Получить пример DeFi данных из DefiLlama (только просмотр)"""
        return await controller.get_sample_defi_data(limit)
    
    @router.get("/sample/yfinance")
    async def get_sample_yfinance_data(limit: int = 10):
        """👀 Получить пример данных из YFinance (только просмотр)"""
        return await controller.get_sample_yfinance_data(limit)
    
    return router