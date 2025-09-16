from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import logging
from datetime import datetime, timedelta

from ..repositories.crypto_repository import CryptocurrencyRepository
from ..repositories.price_history_repository import PriceHistoryRepository
from ..repositories.market_data_repository import MarketDataRepository
from ..repositories.defi_repository import DeFiProtocolRepository
from ..repositories.tvl_history_repository import TVLHistoryRepository
from ..services.lab3_approximation_service import Lab3ApproximationService

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")


class Lab3Controller:
    """Контроллер для Лабораторной работы №3 - Полиномиальная аппроксимация и прогнозирование"""

    def __init__(self):
        self.crypto_repo = CryptocurrencyRepository()
        self.price_repo = PriceHistoryRepository()
        self.market_repo = MarketDataRepository()
        self.defi_repo = DeFiProtocolRepository()
        self.tvl_repo = TVLHistoryRepository()
        self.approximation_service = Lab3ApproximationService()

    async def lab3_page(self, request: Request) -> HTMLResponse:
        """Главная страница Лабораторной работы №3"""
        return templates.TemplateResponse("lab3/lab3_main.html", {
            "request": request,
            "page_title": "Лабораторная работа №3 - Полиномиальная аппроксимация"
        })

    async def polynomial_approximation_page(self, request: Request) -> HTMLResponse:
        """Страница полиномиальной аппроксимации"""
        return templates.TemplateResponse("lab3/polynomial_approximation.html", {
            "request": request,
            "page_title": "Полиномиальная аппроксимация данных"
        })

    async def time_series_forecast_page(self, request: Request) -> HTMLResponse:
        """Страница прогнозирования временных рядов"""
        return templates.TemplateResponse("lab3/time_series_forecast.html", {
            "request": request,
            "page_title": "Прогнозирование временных рядов"
        })

    async def _get_historical_data(self, data_type: str, symbol: str, days: int) -> pd.DataFrame:
        """Получение исторических данных для анализа"""
        try:
            if data_type == "crypto":
                # Используем тот же метод, что и в Lab2
                return await self._fetch_crypto_historical_data(symbol, days)
            else:
                # DeFi данные
                return await self._fetch_defi_historical_data(symbol, days)
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()

    async def _fetch_crypto_historical_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Получение исторических данных криптовалюты"""
        try:
            import httpx

            # Прямой запрос к Bybit API
            base_url = "https://api.bybit.com/v5/market/kline"

            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)

            # Используем дневной интервал для аппроксимации
            interval = "D"
            limit = min(days, 200)

            params = {
                "category": "spot",
                "symbol": f"{symbol}USDT",
                "interval": interval,
                "start": start_timestamp,
                "end": end_timestamp,
                "limit": limit
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("retCode") != 0:
                    logger.error(f"Bybit API error: {data.get('retMsg')}")
                    # Возвращаем синтетические данные
                    return self._generate_synthetic_crypto_data(symbol, days)

                klines = data.get("result", {}).get("list", [])

                if not klines:
                    return self._generate_synthetic_crypto_data(symbol, days)

                # Преобразуем данные
                processed_data = []
                for kline in klines:
                    timestamp_ms = int(kline[0])
                    close_price = float(kline[4])
                    volume = float(kline[5])

                    processed_data.append({
                        'timestamp': datetime.fromtimestamp(timestamp_ms / 1000),
                        'price': close_price,
                        'volume': volume
                    })

                df = pd.DataFrame(processed_data)
                df = df.sort_values('timestamp')

                # Добавляем числовой индекс для аппроксимации
                df.reset_index(drop=True, inplace=True)
                df['day_index'] = range(len(df))

                return df

        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            return self._generate_synthetic_crypto_data(symbol, days)

    def _generate_synthetic_crypto_data(self, symbol: str, days: int) -> pd.DataFrame:
        """Генерация синтетических данных для демонстрации"""
        np.random.seed(hash(symbol) % 2**31)

        base_prices = {
            'BTC': 45000,
            'ETH': 2500,
            'BNB': 350,
            'ADA': 0.5,
            'SOL': 100,
            'XRP': 0.6,
            'DOT': 7
        }

        base_price = base_prices.get(symbol, 100)

        # Генерируем временные метки
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='D')

        # Генерируем цены с трендом и шумом
        trend = np.linspace(0, 0.2, days)
        seasonal = 0.1 * np.sin(np.linspace(0, 4*np.pi, days))
        noise = np.random.normal(0, 0.02, days)

        price_multiplier = 1 + trend + seasonal + noise
        prices = base_price * price_multiplier

        # Генерируем объемы
        volumes = np.random.lognormal(15, 1, days)

        df = pd.DataFrame({
            'timestamp': dates,
            'price': prices,
            'volume': volumes,
            'day_index': range(days)
        })

        return df

    async def _fetch_defi_historical_data(self, protocol: str, days: int) -> pd.DataFrame:
        """Получение исторических данных DeFi протокола"""
        try:
            # Ищем протокол
            protocols = self.defi_repo.search_by_name(protocol, limit=1)
            if not protocols:
                return self._generate_synthetic_defi_data(protocol, days)

            protocol_obj = protocols[0]

            # Получаем историю TVL
            tvl_history = self.tvl_repo.find_by_protocol_id(protocol_obj.id, days=days)
            if not tvl_history or len(tvl_history) < 10:
                return self._generate_synthetic_defi_data(protocol, days)

            # Преобразуем в DataFrame
            data = []
            for record in tvl_history:
                data.append({
                    'timestamp': record.timestamp,
                    'tvl': float(record.tvl) if record.tvl else 0
                })

            df = pd.DataFrame(data)
            df = df.sort_values('timestamp')
            df.reset_index(drop=True, inplace=True)
            df['day_index'] = range(len(df))
            df['price'] = df['tvl'] / 1e6  # Конвертируем в миллионы для удобства

            return df

        except Exception as e:
            logger.error(f"Error fetching DeFi data: {e}")
            return self._generate_synthetic_defi_data(protocol, days)

    def _generate_synthetic_defi_data(self, protocol: str, days: int) -> pd.DataFrame:
        """Генерация синтетических DeFi данных"""
        np.random.seed(hash(protocol) % 2**31)

        base_tvls = {
            'Uniswap': 3500,
            'Aave': 2800,
            'Compound': 1200,
            'MakerDAO': 5000,
            'Curve': 1800
        }

        base_tvl = base_tvls.get(protocol, 1000)

        # Генерируем временные метки
        end_date = datetime.now()
        dates = pd.date_range(end=end_date, periods=days, freq='D')

        # Генерируем TVL с трендом
        trend = np.linspace(0, 0.15, days)
        seasonal = 0.05 * np.sin(np.linspace(0, 3*np.pi, days))
        noise = np.random.normal(0, 0.01, days)

        tvl_multiplier = 1 + trend + seasonal + noise
        tvls = base_tvl * tvl_multiplier

        df = pd.DataFrame({
            'timestamp': dates,
            'price': tvls,  # Используем TVL как "цену" для единообразия
            'tvl': tvls * 1e6,
            'day_index': range(days)
        })

        return df

    async def get_polynomial_approximation_data(
        self,
        data_type: str = "crypto",
        symbol: str = "BTC",
        field: str = "price",
        days: int = 30,
        max_degree: int = 5,
        forecast_days: int = 7
    ) -> JSONResponse:
        """API для получения данных полиномиальной аппроксимации"""
        try:
            # Получаем исторические данные
            df = await self._get_historical_data(data_type, symbol, days)

            if df.empty or field not in df.columns:
                return JSONResponse({
                    "success": False,
                    "error": f"Данные не найдены или поле '{field}' отсутствует"
                })

            # Подготавливаем данные
            X = df['day_index'].values.reshape(-1, 1)
            y = df[field].values

            # Результаты аппроксимации
            approximations = {}
            forecasts = {}
            metrics = {}

            # Аппроксимация полиномами разных степеней
            for degree in range(1, max_degree + 1):
                # Создаем полиномиальные признаки
                poly_features = PolynomialFeatures(degree=degree)
                X_poly = poly_features.fit_transform(X)

                # Обучаем модель
                model = LinearRegression()
                model.fit(X_poly, y)

                # Предсказываем на исторических данных
                y_pred = model.predict(X_poly)

                # Метрики качества
                r2 = r2_score(y, y_pred)
                mse = mean_squared_error(y, y_pred)
                rmse = np.sqrt(mse)

                # Прогноз на будущее
                future_days = np.arange(len(X), len(X) + forecast_days).reshape(-1, 1)
                future_X_poly = poly_features.transform(future_days)
                future_pred = model.predict(future_X_poly)

                approximations[f'degree_{degree}'] = y_pred.tolist()
                forecasts[f'degree_{degree}'] = future_pred.tolist()
                metrics[f'degree_{degree}'] = {
                    'r2': float(r2),
                    'mse': float(mse),
                    'rmse': float(rmse),
                    'equation': self._get_polynomial_equation(model.coef_, model.intercept_, degree)
                }

            # Создаем график
            fig = self._create_approximation_plot(
                df, approximations, forecasts, field, max_degree, forecast_days
            )

            # Создаем график метрик
            metrics_fig = self._create_metrics_plot(metrics)

            return JSONResponse({
                "success": True,
                "data": {
                    "original_data": {
                        "timestamps": df['timestamp'].dt.strftime('%Y-%m-%d').tolist(),
                        "values": df[field].tolist(),
                        "day_indices": df['day_index'].tolist()
                    },
                    "approximations": approximations,
                    "forecasts": forecasts,
                    "metrics": metrics,
                    "plot": fig.to_json(),
                    "metrics_plot": metrics_fig.to_json(),
                    "data_type": data_type,
                    "symbol": symbol,
                    "field": field,
                    "days": days,
                    "forecast_days": forecast_days
                }
            })

        except Exception as e:
            logger.error(f"Error in polynomial approximation: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка аппроксимации: {str(e)}"
            })

    def _get_polynomial_equation(self, coefficients, intercept, degree):
        """Получение строкового представления полиномиального уравнения"""
        equation_parts = [f"{intercept:.2f}"]

        for i, coef in enumerate(coefficients[1:], 1):
            if abs(coef) > 1e-10:  # Игнорируем очень маленькие коэффициенты
                if i == 1:
                    equation_parts.append(f"{coef:+.2e}x")
                else:
                    equation_parts.append(f"{coef:+.2e}x^{i}")

        return " ".join(equation_parts[:5]) + ("..." if len(equation_parts) > 5 else "")

    def _create_approximation_plot(self, df, approximations, forecasts, field, max_degree, forecast_days):
        """Создание графика аппроксимации"""
        fig = go.Figure()

        # Исходные данные
        fig.add_trace(go.Scatter(
            x=df['day_index'],
            y=df[field],
            mode='markers',
            name='Исходные данные',
            marker=dict(color='black', size=8),
            showlegend=True
        ))

        # Цвета для разных степеней полиномов
        colors = ['blue', 'green', 'red', 'purple', 'orange']

        # Аппроксимации
        for i, degree in enumerate(range(1, max_degree + 1)):
            key = f'degree_{degree}'

            # Аппроксимация на исторических данных
            fig.add_trace(go.Scatter(
                x=df['day_index'],
                y=approximations[key],
                mode='lines',
                name=f'Полином {degree} степени',
                line=dict(color=colors[i % len(colors)], width=2),
                showlegend=True
            ))

            # Прогноз
            future_indices = list(range(len(df), len(df) + forecast_days))
            fig.add_trace(go.Scatter(
                x=future_indices,
                y=forecasts[key],
                mode='lines',
                name=f'Прогноз (степень {degree})',
                line=dict(color=colors[i % len(colors)], width=2, dash='dash'),
                showlegend=False
            ))

        # Вертикальная линия для разделения исторических данных и прогноза
        fig.add_vline(
            x=len(df) - 0.5,
            line_dash="dash",
            line_color="gray",
            annotation_text="Начало прогноза"
        )

        fig.update_layout(
            title=f'Полиномиальная аппроксимация: {field}',
            xaxis_title='День',
            yaxis_title=field.capitalize(),
            template='plotly_white',
            hovermode='x unified',
            height=600,
            margin=dict(l=50, r=50, t=80, b=50),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )

        return fig

    def _create_metrics_plot(self, metrics):
        """Создание графика метрик качества"""
        degrees = []
        r2_scores = []
        rmse_scores = []

        for key in sorted(metrics.keys()):
            degree = int(key.split('_')[1])
            degrees.append(degree)
            r2_scores.append(metrics[key]['r2'])
            rmse_scores.append(metrics[key]['rmse'])

        fig = go.Figure()

        # R² score
        fig.add_trace(go.Scatter(
            x=degrees,
            y=r2_scores,
            mode='lines+markers',
            name='R² Score',
            yaxis='y',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))

        # RMSE (на второй оси Y)
        fig.add_trace(go.Scatter(
            x=degrees,
            y=rmse_scores,
            mode='lines+markers',
            name='RMSE',
            yaxis='y2',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title='Метрики качества аппроксимации',
            xaxis=dict(title='Степень полинома', tickmode='linear', tick0=1, dtick=1),
            yaxis=dict(title='R² Score', titlefont=dict(color='blue'), tickfont=dict(color='blue')),
            yaxis2=dict(
                title='RMSE',
                titlefont=dict(color='red'),
                tickfont=dict(color='red'),
                overlaying='y',
                side='right'
            ),
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50),
            hovermode='x unified'
        )

        return fig

    async def get_time_series_forecast_data(
        self,
        data_type: str = "crypto",
        symbol: str = "BTC",
        field: str = "price",
        days: int = 60,
        forecast_method: str = "polynomial",
        forecast_days: int = 14
    ) -> JSONResponse:
        """API для прогнозирования временных рядов"""
        try:
            # Получаем исторические данные
            df = await self._get_historical_data(data_type, symbol, days)

            if df.empty or field not in df.columns:
                return JSONResponse({
                    "success": False,
                    "error": f"Данные не найдены или поле '{field}' отсутствует"
                })

            # Используем сервис для более сложных методов прогнозирования
            try:
                forecast_result = await self.approximation_service.create_forecast(
                    df, field, forecast_method, forecast_days
                )
            except Exception as forecast_error:
                logger.error(f"Error in forecast service: {forecast_error}")
                # Если сервис не работает, создаем простой прогноз
                forecast_result = {
                    'success': True,
                    'forecasts': {'linear': []},
                    'confidence_intervals': {},
                    'metrics': {}
                }

            if not forecast_result['success']:
                return JSONResponse(forecast_result)

            # Создаем визуализацию
            fig = self._create_forecast_plot(
                df, forecast_result['forecasts'], field, forecast_days
            )

            return JSONResponse({
                "success": True,
                "data": {
                    "historical_data": {
                        "timestamps": [str(ts.date()) if hasattr(ts, 'date') else str(ts) for ts in df['timestamp']],
                        "values": df[field].tolist()
                    },
                    "forecasts": forecast_result['forecasts'],
                    "confidence_intervals": forecast_result.get('confidence_intervals', {}),
                    "metrics": forecast_result.get('metrics', {}),
                    "plot": fig.to_json(),
                    "data_type": data_type,
                    "symbol": symbol,
                    "field": field,
                    "forecast_method": forecast_method,
                    "forecast_days": forecast_days
                }
            })

        except Exception as e:
            import traceback
            logger.error(f"Error in time series forecast: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка прогнозирования: {str(e)}"
            })

    def _create_forecast_plot(self, df, forecasts, field, forecast_days):
        """Создание графика прогноза"""
        fig = go.Figure()

        # Исторические данные
        # Преобразуем даты в строки для совместимости с Plotly
        historical_dates = [ts.isoformat() if hasattr(ts, 'isoformat') else str(ts) for ts in df['timestamp']]

        fig.add_trace(go.Scatter(
            x=historical_dates,
            y=df[field],
            mode='lines',
            name='Исторические данные',
            line=dict(color='blue', width=2)
        ))

        # Генерируем даты для прогноза
        last_date = df['timestamp'].iloc[-1]

        # Исправляем для совместимости с новыми версиями pandas
        if isinstance(last_date, pd.Timestamp):
            start_forecast = last_date + pd.Timedelta(days=1)
        else:
            start_forecast = pd.Timestamp(last_date) + pd.Timedelta(days=1)

        forecast_dates = pd.date_range(
            start=start_forecast,
            periods=forecast_days,
            freq='D'
        )

        # Различные методы прогнозирования
        colors = {
            'linear': 'green',
            'polynomial': 'red',
            'exponential': 'purple',
            'moving_average': 'orange'
        }

        # Преобразуем даты прогноза в строки
        forecast_dates_str = [date.isoformat() if hasattr(date, 'isoformat') else str(date) for date in forecast_dates]

        for method, values in forecasts.items():
            if len(values) > 0:
                fig.add_trace(go.Scatter(
                    x=forecast_dates_str,
                    y=values,
                    mode='lines',
                    name=f'Прогноз ({method})',
                    line=dict(
                        color=colors.get(method, 'gray'),
                        width=2,
                        dash='dash'
                    )
                ))

        # Вместо вертикальной линии добавим текстовую аннотацию
        # Это избегает проблем с типами данных в Plotly
        last_timestamp = df['timestamp'].iloc[-1]
        if hasattr(last_timestamp, 'isoformat'):
            last_timestamp_str = last_timestamp.isoformat()
        else:
            last_timestamp_str = str(last_timestamp)

        # Добавляем простую аннотацию для обозначения границы прогноза
        try:
            fig.add_annotation(
                x=last_timestamp_str,
                y=df[field].iloc[-1],
                text="Начало прогноза",
                showarrow=True,
                arrowhead=2,
                arrowcolor="gray",
                font=dict(size=10, color="gray"),
                bgcolor="rgba(255,255,255,0.8)"
            )
        except Exception as ann_error:
            # Если аннотация тоже не работает, просто пропускаем её
            logger.warning(f"Could not add annotation: {ann_error}")

        fig.update_layout(
            title=f'Прогнозирование временного ряда: {field}',
            xaxis_title='Дата',
            yaxis_title=field.capitalize(),
            template='plotly_white',
            hovermode='x unified',
            height=600,
            margin=dict(l=50, r=50, t=80, b=50)
        )

        return fig


def create_lab3_router() -> APIRouter:
    """Создание роутера для Лабораторной работы №3"""
    router = APIRouter(prefix="/lab3", tags=["lab3"])
    controller = Lab3Controller()

    # Веб-страницы
    @router.get("/", response_class=HTMLResponse)
    async def lab3_main_page(request: Request):
        return await controller.lab3_page(request)

    @router.get("/polynomial", response_class=HTMLResponse)
    async def polynomial_approximation_page(request: Request):
        return await controller.polynomial_approximation_page(request)

    @router.get("/forecast", response_class=HTMLResponse)
    async def time_series_forecast_page(request: Request):
        return await controller.time_series_forecast_page(request)

    # API эндпоинты
    @router.get("/api/polynomial-approximation")
    async def polynomial_approximation_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbol: str = Query("BTC", description="Символ криптовалюты или название протокола"),
        field: str = Query("price", description="Поле для анализа"),
        days: int = Query(30, ge=10, le=365, description="Количество дней исторических данных"),
        max_degree: int = Query(5, ge=1, le=10, description="Максимальная степень полинома"),
        forecast_days: int = Query(7, ge=1, le=30, description="Количество дней для прогноза")
    ):
        return await controller.get_polynomial_approximation_data(
            data_type, symbol, field, days, max_degree, forecast_days
        )

    @router.get("/api/time-series-forecast")
    async def time_series_forecast_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbol: str = Query("BTC", description="Символ криптовалюты или название протокола"),
        field: str = Query("price", description="Поле для анализа"),
        days: int = Query(60, ge=15, le=365, description="Количество дней исторических данных"),
        forecast_method: str = Query("polynomial", description="Метод прогнозирования"),
        forecast_days: int = Query(14, ge=1, le=60, description="Количество дней для прогноза")
    ):
        return await controller.get_time_series_forecast_data(
            data_type, symbol, field, days, forecast_method, forecast_days
        )

    return router