from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
from sklearn.preprocessing import StandardScaler
import logging
import json

from ..repositories.crypto_repository import CryptocurrencyRepository
from ..repositories.price_history_repository import PriceHistoryRepository
from ..repositories.market_data_repository import MarketDataRepository
from ..repositories.defi_repository import DeFiProtocolRepository
from ..repositories.tvl_history_repository import TVLHistoryRepository

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")


class Lab2Controller:
    """Контроллер для Лабораторной работы №2 - Статистический анализ данных"""

    def __init__(self):
        self.crypto_repo = CryptocurrencyRepository()
        self.price_repo = PriceHistoryRepository()
        self.market_repo = MarketDataRepository()
        self.defi_repo = DeFiProtocolRepository()
        self.tvl_repo = TVLHistoryRepository()

    async def lab2_page(self, request: Request) -> HTMLResponse:
        """Главная страница Лабораторной работы №2"""
        return templates.TemplateResponse("lab2/lab2_main.html", {
            "request": request,
            "page_title": "Лабораторная работа №2 - Статистический анализ"
        })

    async def normality_testing_page(self, request: Request) -> HTMLResponse:
        """Страница проверки на нормальность"""
        return templates.TemplateResponse("lab2/normality_testing.html", {
            "request": request,
            "page_title": "Проверка данных на нормальность"
        })

    async def correlation_analysis_page(self, request: Request) -> HTMLResponse:
        """Страница корреляционного анализа"""
        return templates.TemplateResponse("lab2/correlation_analysis.html", {
            "request": request,
            "page_title": "Корреляционный анализ"
        })

    async def _get_crypto_data_for_analysis(self, crypto_symbol: str = "BTC", days: int = 30) -> pd.DataFrame:
        """Получение данных криптовалюты для анализа с прямыми запросами к Bybit API"""
        try:
            logger.info(f"Fetching fresh data for {crypto_symbol} for {days} days from Bybit API")

            # Прямой запрос к Bybit API для получения исторических данных
            df = await self._fetch_bybit_historical_data(crypto_symbol, days)

            if df.empty:
                logger.warning(f"No data from Bybit API for {crypto_symbol}")
                return pd.DataFrame()

            logger.info(f"Successfully fetched {len(df)} data points for {crypto_symbol}")
            return df

        except Exception as e:
            logger.error(f"Error getting crypto data for analysis: {e}")
            return pd.DataFrame()

    async def _fetch_bybit_historical_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Получение исторических данных с Bybit API"""
        try:
            import httpx
            from datetime import datetime, timedelta

            # Параметры для Bybit API
            base_url = "https://api.bybit.com/v5/market/kline"

            # Вычисляем временные рамки
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            # Конвертируем в timestamp (миллисекунды)
            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)

            # Определяем интервал в зависимости от периода
            if days <= 7:
                interval = "60"  # 1 час
                limit = days * 24
            elif days <= 30:
                interval = "240"  # 4 часа
                limit = days * 6
            else:
                interval = "D"   # 1 день
                limit = days

            limit = min(limit, 1000)  # Максимальный лимит Bybit

            params = {
                "category": "spot",
                "symbol": f"{symbol}USDT",
                "interval": interval,
                "start": start_timestamp,
                "end": end_timestamp,
                "limit": limit
            }

            logger.info(f"Requesting Bybit data: {params}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("retCode") != 0:
                    logger.error(f"Bybit API error: {data.get('retMsg')}")
                    return pd.DataFrame()

                klines = data.get("result", {}).get("list", [])

                if not klines:
                    logger.warning(f"No kline data returned for {symbol}")
                    return pd.DataFrame()

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
                        'price_usd': close_price,
                        'open_price': open_price,
                        'high_price': high_price,
                        'low_price': low_price,
                        'volume_24h': volume,
                        'turnover_24h': turnover,
                        'market_cap': close_price * 1e9,  # Примерная оценка
                        'price_change_24h': 0  # Будет вычислено позже
                    })

                # Создаем DataFrame
                df = pd.DataFrame(processed_data)
                df = df.sort_values('timestamp')

                # Вычисляем производные метрики
                if len(df) > 1:
                    df['price_returns'] = df['price_usd'].pct_change()
                    df['log_returns'] = np.log(df['price_usd'] / df['price_usd'].shift(1))
                    df['volatility'] = df['price_returns'].rolling(window=min(7, len(df)//2), min_periods=1).std()

                    # Вычисляем изменение цены за 24ч
                    df['price_change_24h'] = df['price_returns'] * 100

                return df.dropna()

        except Exception as e:
            logger.error(f"Error fetching Bybit data for {symbol}: {e}")
            return pd.DataFrame()

    def _generate_demo_crypto_data(self, crypto_symbol: str, days: int = 30) -> pd.DataFrame:
        """Генерация демонстрационных данных для анализа"""
        try:
            import datetime
            from datetime import timedelta

            logger.info(f"Generating demo data for {crypto_symbol} with {days} days")

            # Параметры для разных криптовалют
            base_prices = {
                'PEPE': 0.000012,
                'SHIB': 0.000008,
                'BONK': 0.000015,
                'MOG': 0.000002,
                'COQ': 0.000005,
                'BTT': 0.0000008,
                'SATS': 0.00000004
            }

            base_price = base_prices.get(crypto_symbol, 0.00001)

            # Генерируем временные метки
            end_date = datetime.datetime.now()
            start_date = end_date - timedelta(days=days)

            # Создаем почасовые данные
            timestamps = []
            current_time = start_date
            while current_time <= end_date:
                timestamps.append(current_time)
                current_time += timedelta(hours=1)

            n_points = len(timestamps)

            # Генерируем случайные цены с трендом
            np.random.seed(hash(crypto_symbol) % 2**31)  # Воспроизводимые результаты

            # Генерируем случайное блуждание
            returns = np.random.normal(0.0, 0.03, n_points)  # 3% волатильность

            # Добавляем автокорреляцию для реалистичности
            for i in range(1, len(returns)):
                returns[i] += 0.1 * returns[i-1]

            # Вычисляем цены
            prices = [base_price]
            for i in range(1, n_points):
                new_price = prices[-1] * (1 + returns[i])
                prices.append(max(new_price, base_price * 0.1))  # Минимальная цена

            # Генерируем объемы торгов
            volumes = np.random.lognormal(15, 1, n_points)  # Лог-нормальное распределение

            # Создаем DataFrame
            data = []
            for i, timestamp in enumerate(timestamps):
                data.append({
                    'timestamp': timestamp,
                    'price_usd': prices[i],
                    'volume_24h': volumes[i],
                    'market_cap': prices[i] * 1e12,  # Примерная капитализация
                    'price_change_24h': returns[i] * 100 if i > 0 else 0
                })

            df = pd.DataFrame(data)

            # Вычисляем производные метрики
            df['price_returns'] = df['price_usd'].pct_change()
            df['log_returns'] = np.log(df['price_usd'] / df['price_usd'].shift(1))
            df['volatility'] = df['price_returns'].rolling(window=7, min_periods=1).std()

            logger.info(f"Generated {len(df)} demo data points for {crypto_symbol}")
            return df.dropna()

        except Exception as e:
            logger.error(f"Error generating demo data: {e}")
            return pd.DataFrame()

    async def _get_defi_data_for_analysis(self, protocol_name: str = "Uniswap", days: int = 30) -> pd.DataFrame:
        """Получение данных DeFi протокола для анализа"""
        try:
            # Находим протокол по имени
            protocols = self.defi_repo.search_by_name(protocol_name, limit=1)
            if not protocols:
                logger.warning(f"DeFi protocol {protocol_name} not found")
                return self._generate_demo_defi_data(protocol_name, days)

            protocol = protocols[0]

            # Получаем историю TVL
            tvl_history = self.tvl_repo.find_by_protocol_id(protocol.id, days=days)
            if not tvl_history or len(tvl_history) < 10:
                logger.warning(f"Insufficient TVL history for {protocol_name}, generating demo data")
                return self._generate_demo_defi_data(protocol_name, days)

            # Преобразуем в DataFrame
            data = []
            for record in tvl_history:
                data.append({
                    'timestamp': record.timestamp,
                    'tvl': float(record.tvl) if record.tvl else 0,
                    'tvl_change_24h': float(record.tvl_change_24h) if record.tvl_change_24h else 0
                })

            df = pd.DataFrame(data)
            df = df.sort_values('timestamp')

            # Вычисляем дополнительные метрики
            if len(df) > 1:
                df['tvl_returns'] = df['tvl'].pct_change()
                df['log_tvl'] = np.log(df['tvl'])
                df['tvl_volatility'] = df['tvl_returns'].rolling(window=7).std()

            return df.dropna()

        except Exception as e:
            logger.error(f"Error getting DeFi data for analysis: {e}")
            return self._generate_demo_defi_data(protocol_name, days)

    def _generate_demo_defi_data(self, protocol_name: str, days: int = 30) -> pd.DataFrame:
        """Генерация демонстрационных данных для DeFi протокола"""
        try:
            import datetime
            from datetime import timedelta

            logger.info(f"Generating demo DeFi data for {protocol_name} with {days} days")

            # Параметры для разных протоколов
            base_tvls = {
                'Uniswap': 3500000000,    # $3.5B
                'Aave': 2800000000,       # $2.8B
                'Compound': 1200000000,   # $1.2B
                'MakerDAO': 5000000000,   # $5B
                'Curve': 1800000000       # $1.8B
            }

            base_tvl = base_tvls.get(protocol_name, 1000000000)

            # Генерируем временные метки (каждые 6 часов)
            end_date = datetime.datetime.now()
            start_date = end_date - timedelta(days=days)

            timestamps = []
            current_time = start_date
            while current_time <= end_date:
                timestamps.append(current_time)
                current_time += timedelta(hours=6)

            n_points = len(timestamps)

            # Генерируем случайные изменения TVL
            np.random.seed(hash(protocol_name) % 2**31)  # Воспроизводимые результаты

            # TVL имеет меньшую волатильность чем цены
            returns = np.random.normal(0.0, 0.015, n_points)  # 1.5% волатильность

            # Добавляем автокорреляцию
            for i in range(1, len(returns)):
                returns[i] += 0.2 * returns[i-1]

            # Вычисляем TVL
            tvls = [base_tvl]
            for i in range(1, n_points):
                new_tvl = tvls[-1] * (1 + returns[i])
                tvls.append(max(new_tvl, base_tvl * 0.3))  # Минимальный TVL

            # Создаем DataFrame
            data = []
            for i, timestamp in enumerate(timestamps):
                data.append({
                    'timestamp': timestamp,
                    'tvl': tvls[i],
                    'tvl_change_24h': returns[i] * 100 if i > 0 else 0
                })

            df = pd.DataFrame(data)

            # Вычисляем производные метрики
            df['tvl_returns'] = df['tvl'].pct_change()
            df['log_tvl'] = np.log(df['tvl'])
            df['tvl_volatility'] = df['tvl_returns'].rolling(window=4, min_periods=1).std()

            logger.info(f"Generated {len(df)} demo DeFi data points for {protocol_name}")
            return df.dropna()

        except Exception as e:
            logger.error(f"Error generating demo DeFi data: {e}")
            return pd.DataFrame()

    async def get_normality_test_data(
        self,
        data_type: str = "crypto",
        symbol: str = "BTC",
        field: str = "price_returns",
        days: int = 30
    ) -> JSONResponse:
        """API для получения данных теста на нормальность"""
        try:
            if data_type == "crypto":
                df = await self._get_crypto_data_for_analysis(symbol, days)
            else:
                df = await self._get_defi_data_for_analysis(symbol, days)

            if df.empty or field not in df.columns:
                return JSONResponse({
                    "success": False,
                    "error": f"Данные не найдены или поле '{field}' отсутствует"
                })

            data_series = df[field].dropna()

            if len(data_series) < 10:
                return JSONResponse({
                    "success": False,
                    "error": "Недостаточно данных для анализа (минимум 10 наблюдений)"
                })

            # Статистические тесты на нормальность
            shapiro_stat, shapiro_p = stats.shapiro(data_series)
            ks_stat, ks_p = stats.kstest(data_series, 'norm', args=(data_series.mean(), data_series.std()))
            jb_stat, jb_p = stats.jarque_bera(data_series)

            # Создание гистограммы
            fig_hist = go.Figure()

            # Гистограмма данных
            fig_hist.add_trace(go.Histogram(
                x=data_series,
                nbinsx=30,
                name='Фактические данные',
                opacity=0.7,
                histnorm='probability density',
                marker_color='lightblue'
            ))

            # Нормальное распределение для сравнения
            x_norm = np.linspace(data_series.min(), data_series.max(), 100)
            y_norm = stats.norm.pdf(x_norm, data_series.mean(), data_series.std())

            fig_hist.add_trace(go.Scatter(
                x=x_norm,
                y=y_norm,
                mode='lines',
                name='Нормальное распределение',
                line=dict(color='red', width=2)
            ))

            fig_hist.update_layout(
                title=f'Гистограмма распределения: {field}',
                xaxis_title=field,
                yaxis_title='Плотность вероятности',
                showlegend=True,
                template='plotly_white'
            )

            # Q-Q plot (график квантилей)
            fig_qq = go.Figure()

            # Вычисляем квантили
            theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(data_series)))
            sample_quantiles = np.sort(data_series)

            fig_qq.add_trace(go.Scatter(
                x=theoretical_quantiles,
                y=sample_quantiles,
                mode='markers',
                name='Квантили данных',
                marker=dict(color='blue', size=6)
            ))

            # Линия идеального соответствия
            min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
            max_val = max(theoretical_quantiles.max(), sample_quantiles.max())

            fig_qq.add_trace(go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Линия нормальности',
                line=dict(color='red', width=2, dash='dash')
            ))

            fig_qq.update_layout(
                title='Q-Q график (График квантилей)',
                xaxis_title='Теоретические квантили (нормальное распределение)',
                yaxis_title='Выборочные квантили',
                showlegend=True,
                template='plotly_white'
            )

            # Базовая статистика
            basic_stats = {
                'mean': float(data_series.mean()),
                'median': float(data_series.median()),
                'std': float(data_series.std()),
                'skewness': float(stats.skew(data_series)),
                'kurtosis': float(stats.kurtosis(data_series)),
                'min': float(data_series.min()),
                'max': float(data_series.max()),
                'count': len(data_series)
            }

            # Тесты на нормальность
            normality_tests = {
                'shapiro': {
                    'statistic': float(shapiro_stat),
                    'p_value': float(shapiro_p),
                    'interpretation': 'Данные нормально распределены' if shapiro_p > 0.05 else 'Данные НЕ нормально распределены'
                },
                'kolmogorov_smirnov': {
                    'statistic': float(ks_stat),
                    'p_value': float(ks_p),
                    'interpretation': 'Данные нормально распределены' if ks_p > 0.05 else 'Данные НЕ нормально распределены'
                },
                'jarque_bera': {
                    'statistic': float(jb_stat),
                    'p_value': float(jb_p),
                    'interpretation': 'Данные нормально распределены' if jb_p > 0.05 else 'Данные НЕ нормально распределены'
                }
            }

            return JSONResponse({
                "success": True,
                "data": {
                    "histogram": fig_hist.to_json(),
                    "qq_plot": fig_qq.to_json(),
                    "basic_stats": basic_stats,
                    "normality_tests": normality_tests,
                    "data_type": data_type,
                    "symbol": symbol,
                    "field": field,
                    "days": days
                }
            })

        except Exception as e:
            logger.error(f"Error in normality test: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка анализа данных: {str(e)}"
            })

    async def get_correlation_analysis_data(
        self,
        data_type: str = "crypto",
        symbols: List[str] = None,
        fields: List[str] = None,
        days: int = 30
    ) -> JSONResponse:
        """API для корреляционного анализа"""
        try:
            if not symbols:
                symbols = ["BTC", "ETH", "BNB"] if data_type == "crypto" else ["Uniswap", "Aave", "Compound"]

            if not fields:
                fields = ["price_usd", "volume_24h", "market_cap"] if data_type == "crypto" else ["tvl", "tvl_change_24h"]

            # Собираем данные для корреляционного анализа
            correlation_data = {}

            for symbol in symbols:
                if data_type == "crypto":
                    df = await self._get_crypto_data_for_analysis(symbol, days)
                else:
                    df = await self._get_defi_data_for_analysis(symbol, days)

                if not df.empty:
                    for field in fields:
                        if field in df.columns:
                            key = f"{symbol}_{field}"
                            correlation_data[key] = df[field].values

            if len(correlation_data) < 2:
                return JSONResponse({
                    "success": False,
                    "error": "Недостаточно данных для корреляционного анализа"
                })

            # Создаем DataFrame для корреляционного анализа
            max_len = max(len(v) for v in correlation_data.values())

            # Выравниваем длины массивов
            for key in correlation_data:
                data = correlation_data[key]
                if len(data) < max_len:
                    # Дополняем NaN для коротких серий
                    padded_data = np.full(max_len, np.nan)
                    padded_data[:len(data)] = data
                    correlation_data[key] = padded_data
                elif len(data) > max_len:
                    # Обрезаем для длинных серий
                    correlation_data[key] = data[:max_len]

            corr_df = pd.DataFrame(correlation_data)

            # Вычисляем корреляционную матрицу
            correlation_matrix = corr_df.corr()

            # Создаем тепловую карту корреляций
            fig_heatmap = px.imshow(
                correlation_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Корреляционная матрица"
            )

            fig_heatmap.update_layout(
                title="Корреляционная матрица данных",
                template='plotly_white'
            )

            # Создаем scatter plot matrix для парных корреляций
            fig_scatter = make_subplots(
                rows=len(correlation_matrix.columns),
                cols=len(correlation_matrix.columns),
                subplot_titles=[f"vs {col}" for col in correlation_matrix.columns]
            )

            # Выбираем топ коррелирующие пары для scatter plots
            correlation_pairs = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    col1 = correlation_matrix.columns[i]
                    col2 = correlation_matrix.columns[j]
                    corr_value = correlation_matrix.iloc[i, j]
                    if not np.isnan(corr_value):
                        correlation_pairs.append({
                            'var1': col1,
                            'var2': col2,
                            'correlation': corr_value,
                            'abs_correlation': abs(corr_value)
                        })

            # Сортируем по убыванию абсолютной корреляции
            correlation_pairs.sort(key=lambda x: x['abs_correlation'], reverse=True)

            # Создаем простой scatter plot для топ-3 корреляций
            scatter_plots = []
            for i, pair in enumerate(correlation_pairs[:3]):
                var1, var2 = pair['var1'], pair['var2']
                if var1 in corr_df.columns and var2 in corr_df.columns:
                    clean_data = corr_df[[var1, var2]].dropna()
                    if len(clean_data) > 5:
                        fig_scatter_single = px.scatter(
                            clean_data,
                            x=var1,
                            y=var2,
                            title=f"Корреляция: {var1} vs {var2} (r={pair['correlation']:.3f})"
                        )
                        scatter_plots.append({
                            'plot': fig_scatter_single.to_json(),
                            'correlation': pair['correlation'],
                            'var1': var1,
                            'var2': var2
                        })

            # Статистика корреляций
            correlation_stats = {
                'matrix': correlation_matrix.to_dict(),
                'strongest_positive': max(correlation_pairs, key=lambda x: x['correlation']) if correlation_pairs else None,
                'strongest_negative': min(correlation_pairs, key=lambda x: x['correlation']) if correlation_pairs else None,
                'average_correlation': np.nanmean([p['correlation'] for p in correlation_pairs]),
                'total_pairs': len(correlation_pairs)
            }

            return JSONResponse({
                "success": True,
                "data": {
                    "heatmap": fig_heatmap.to_json(),
                    "scatter_plots": scatter_plots,
                    "correlation_matrix": correlation_matrix.to_dict(),
                    "correlation_stats": correlation_stats,
                    "data_type": data_type,
                    "symbols": symbols,
                    "fields": fields,
                    "days": days
                }
            })

        except Exception as e:
            logger.error(f"Error in correlation analysis: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка корреляционного анализа: {str(e)}"
            })


def create_lab2_router() -> APIRouter:
    """Создание роутера для Лабораторной работы №2"""
    router = APIRouter(prefix="/lab2", tags=["lab2"])
    controller = Lab2Controller()

    # Веб-страницы
    @router.get("/", response_class=HTMLResponse)
    async def lab2_main_page(request: Request):
        return await controller.lab2_page(request)

    @router.get("/normality", response_class=HTMLResponse)
    async def normality_testing_page(request: Request):
        return await controller.normality_testing_page(request)

    @router.get("/correlation", response_class=HTMLResponse)
    async def correlation_analysis_page(request: Request):
        return await controller.correlation_analysis_page(request)

    # API эндпоинты
    @router.get("/api/normality-test")
    async def normality_test_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbol: str = Query("BTC", description="Символ криптовалюты или название протокола"),
        field: str = Query("price_returns", description="Поле для анализа"),
        days: int = Query(30, ge=7, le=365, description="Количество дней для анализа")
    ):
        return await controller.get_normality_test_data(data_type, symbol, field, days)

    @router.post("/api/correlation-analysis")
    async def correlation_analysis_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbols: str = Query("BTC,ETH,BNB", description="Символы через запятую"),
        fields: str = Query("price_usd,volume_24h", description="Поля через запятую"),
        days: int = Query(30, ge=7, le=365, description="Количество дней для анализа")
    ):
        symbols_list = [s.strip() for s in symbols.split(",")]
        fields_list = [f.strip() for f in fields.split(",")]
        return await controller.get_correlation_analysis_data(data_type, symbols_list, fields_list, days)

    return router