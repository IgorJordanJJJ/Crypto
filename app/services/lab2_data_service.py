import pandas as pd
import numpy as np
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from ..repositories.lab2_cache_repository import Lab2CacheRepository

logger = logging.getLogger(__name__)


class Lab2DataService:
    """Сервис для получения и кэширования данных для Лабораторной работы №2"""

    def __init__(self):
        self.cache_repo = Lab2CacheRepository()

    async def get_crypto_data(
        self,
        symbol: str,
        days: int,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """Получение данных криптовалюты с кэшированием"""
        try:
            # Определяем интервал
            interval = self._determine_interval(days)

            logger.info(f"Getting crypto data for {symbol}, {days} days, interval {interval}")

            # Проверяем кэш, если не принудительное обновление
            if not force_refresh:
                cached_data = self._get_cached_data(symbol, "crypto", interval, days)
                if cached_data is not None and not cached_data.empty:
                    logger.info(f"Using cached data for {symbol}")
                    return cached_data

            # Получаем свежие данные с Bybit
            logger.info(f"Fetching fresh data from Bybit for {symbol}")
            fresh_data = await self._fetch_bybit_data(symbol, interval, days)

            if fresh_data:
                # Сохраняем в кэш
                saved_count = self.cache_repo.save_cached_data(
                    fresh_data, symbol, "crypto", interval
                )
                logger.info(f"Saved {saved_count} records to cache")

                # Преобразуем в DataFrame для анализа
                return self._process_crypto_data(fresh_data)

            else:
                logger.warning(f"No fresh data obtained for {symbol}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error getting crypto data for {symbol}: {e}")
            return pd.DataFrame()

    def _determine_interval(self, days: int) -> str:
        """Определение интервала на основе количества дней"""
        if days <= 7:
            return "60"  # 1 час
        elif days <= 30:
            return "240"  # 4 часа
        else:
            return "D"   # 1 день

    def _get_cached_data(
        self,
        symbol: str,
        data_type: str,
        interval: str,
        days: int
    ) -> Optional[pd.DataFrame]:
        """Получение данных из кэша"""
        try:
            # Проверяем свежесть данных
            if not self.cache_repo.is_data_fresh(symbol, data_type, interval, days):
                logger.info(f"Cached data for {symbol} is not fresh")
                return None

            # Получаем данные из кэша
            cached_records = self.cache_repo.find_cached_data(symbol, data_type, interval, days)

            if not cached_records:
                logger.info(f"No cached data found for {symbol}")
                return None

            # Преобразуем в список словарей
            data_list = []
            for record in cached_records:
                data_list.append({
                    'timestamp': record.timestamp,
                    'open_price': record.open_price,
                    'high_price': record.high_price,
                    'low_price': record.low_price,
                    'close_price': record.close_price,
                    'volume': record.volume,
                    'turnover': record.turnover
                })

            return self._process_crypto_data(data_list)

        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None

    async def _fetch_bybit_data(
        self,
        symbol: str,
        interval: str,
        days: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Получение данных с Bybit API"""
        try:
            # Параметры для Bybit API
            base_url = "https://api.bybit.com/v5/market/kline"

            # Вычисляем временные рамки
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            # Конвертируем в timestamp (миллисекунды)
            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)

            # Определяем лимит
            if interval == "60":  # 1 час
                limit = min(days * 24, 1000)
            elif interval == "240":  # 4 часа
                limit = min(days * 6, 1000)
            else:  # 1 день
                limit = min(days, 1000)

            params = {
                "category": "spot",
                "symbol": f"{symbol}USDT",
                "interval": interval,
                "start": start_timestamp,
                "end": end_timestamp,
                "limit": limit
            }

            logger.info(f"Requesting Bybit data with params: {params}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("retCode") != 0:
                    logger.error(f"Bybit API error: {data.get('retMsg')}")
                    return None

                klines = data.get("result", {}).get("list", [])

                if not klines:
                    logger.warning(f"No kline data returned for {symbol}")
                    return None

                # Преобразуем данные
                processed_data = []
                for kline in klines:
                    timestamp_ms = int(kline[0])
                    open_price = float(kline[1])
                    high_price = float(kline[2])
                    low_price = float(kline[3])
                    close_price = float(kline[4])
                    volume = float(kline[5])
                    turnover = float(kline[6])

                    processed_data.append({
                        'timestamp': datetime.fromtimestamp(timestamp_ms / 1000),
                        'open_price': open_price,
                        'high_price': high_price,
                        'low_price': low_price,
                        'close_price': close_price,
                        'volume': volume,
                        'turnover': turnover
                    })

                logger.info(f"Successfully fetched {len(processed_data)} records from Bybit")
                return processed_data

        except Exception as e:
            logger.error(f"Error fetching Bybit data for {symbol}: {e}")
            return None

    def _process_crypto_data(self, data_list: List[Dict[str, Any]]) -> pd.DataFrame:
        """Обработка данных криптовалюты для анализа"""
        try:
            if not data_list:
                return pd.DataFrame()

            # Создаем DataFrame
            df = pd.DataFrame(data_list)
            df = df.sort_values('timestamp')

            # Переименовываем колонки для совместимости с Lab2
            df['price_usd'] = df['close_price']
            df['volume_24h'] = df['volume']
            df['turnover_24h'] = df['turnover']
            df['market_cap'] = df['close_price'] * 1e9  # Примерная оценка

            # Вычисляем производные метрики
            if len(df) > 1:
                df['price_returns'] = df['price_usd'].pct_change()
                df['log_returns'] = np.log(df['price_usd'] / df['price_usd'].shift(1))
                df['volatility'] = df['price_returns'].rolling(
                    window=min(7, len(df)//2),
                    min_periods=1
                ).std()

                # Вычисляем изменение цены за 24ч
                df['price_change_24h'] = df['price_returns'] * 100

            logger.info(f"Processed {len(df)} data points, columns: {list(df.columns)}")
            return df.dropna()

        except Exception as e:
            logger.error(f"Error processing crypto data: {e}")
            return pd.DataFrame()

    async def get_defi_data(
        self,
        protocol_name: str,
        days: int,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """Получение данных DeFi протокола (пока что возвращаем пустой DataFrame)"""
        # TODO: Реализовать для DeFi протоколов
        logger.info(f"DeFi data requested for {protocol_name}, but not implemented yet")
        return pd.DataFrame()

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Получение статистики кэша"""
        try:
            stats = self.cache_repo.get_cache_stats()
            return {
                'status': 'success',
                'cache_stats': stats
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def refresh_symbol_data(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Принудительное обновление данных для символа"""
        try:
            logger.info(f"Force refreshing data for {symbol}")
            df = await self.get_crypto_data(symbol, days, force_refresh=True)

            return {
                'status': 'success',
                'symbol': symbol,
                'records_fetched': len(df),
                'message': f"Successfully refreshed {len(df)} records for {symbol}"
            }

        except Exception as e:
            logger.error(f"Error refreshing data for {symbol}: {e}")
            return {
                'status': 'error',
                'symbol': symbol,
                'error': str(e)
            }

    def cleanup_old_cache(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Очистка старого кэша"""
        try:
            deleted_count = self.cache_repo.cleanup_old_data(days_to_keep)
            return {
                'status': 'success',
                'deleted_records': deleted_count,
                'message': f"Cleaned up {deleted_count} old cache records"
            }
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }