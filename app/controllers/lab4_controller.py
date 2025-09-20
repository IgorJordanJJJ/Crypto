from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.manifold import TSNE
import logging
from datetime import datetime, timedelta

from ..repositories.crypto_repository import CryptocurrencyRepository
from ..repositories.price_history_repository import PriceHistoryRepository
from ..repositories.market_data_repository import MarketDataRepository
from ..repositories.defi_repository import DeFiProtocolRepository
from ..repositories.tvl_history_repository import TVLHistoryRepository

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="app/templates")


class Lab4Controller:
    """Контроллер для Лабораторной работы №4 - Кластеризация данных"""

    def __init__(self):
        self.crypto_repo = CryptocurrencyRepository()
        self.price_repo = PriceHistoryRepository()
        self.market_repo = MarketDataRepository()
        self.defi_repo = DeFiProtocolRepository()
        self.tvl_repo = TVLHistoryRepository()

    async def lab4_page(self, request: Request) -> HTMLResponse:
        """Главная страница Лабораторной работы №4"""
        return templates.TemplateResponse("lab4/lab4_main.html", {
            "request": request,
            "page_title": "Лабораторная работа №4 - Кластеризация данных"
        })

    async def kmeans_clustering_page(self, request: Request) -> HTMLResponse:
        """Страница K-means кластеризации"""
        return templates.TemplateResponse("lab4/kmeans_clustering.html", {
            "request": request,
            "page_title": "K-means кластеризация"
        })

    async def dbscan_clustering_page(self, request: Request) -> HTMLResponse:
        """Страница DBSCAN кластеризации"""
        return templates.TemplateResponse("lab4/dbscan_clustering.html", {
            "request": request,
            "page_title": "DBSCAN кластеризация"
        })

    async def hierarchical_clustering_page(self, request: Request) -> HTMLResponse:
        """Страница иерархической кластеризации"""
        return templates.TemplateResponse("lab4/hierarchical_clustering.html", {
            "request": request,
            "page_title": "Иерархическая кластеризация"
        })

    async def clustering_comparison_page(self, request: Request) -> HTMLResponse:
        """Страница сравнения методов кластеризации"""
        return templates.TemplateResponse("lab4/clustering_comparison.html", {
            "request": request,
            "page_title": "Сравнение методов кластеризации"
        })

    async def _get_clustering_data(self, data_type: str, symbols: List[str], days: int) -> pd.DataFrame:
        """Получение данных для кластеризации"""
        try:
            all_data = []

            if data_type == "crypto":
                # Получаем данные криптовалют
                for symbol in symbols:
                    crypto_data = await self._fetch_crypto_data_for_clustering(symbol, days)
                    if not crypto_data.empty:
                        crypto_data['symbol'] = symbol
                        all_data.append(crypto_data)
            else:
                # Получаем данные DeFi протоколов
                for symbol in symbols:
                    defi_data = await self._fetch_defi_data_for_clustering(symbol, days)
                    if not defi_data.empty:
                        defi_data['symbol'] = symbol
                        all_data.append(defi_data)

            if not all_data:
                return pd.DataFrame()

            # Объединяем данные
            combined_df = pd.concat(all_data, ignore_index=True)

            # Очищаем DataFrame от NaN и Inf значений
            combined_df = combined_df.replace([np.inf, -np.inf], 0)
            combined_df = combined_df.fillna(0)

            return combined_df

        except Exception as e:
            logger.error(f"Error getting clustering data: {e}")
            return pd.DataFrame()

    async def _fetch_crypto_data_for_clustering(self, symbol: str, days: int) -> pd.DataFrame:
        """Получение данных криптовалюты для кластеризации"""
        try:
            import httpx

            # Получаем исторические данные с Bybit
            base_url = "https://api.bybit.com/v5/market/kline"

            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)

            params = {
                "category": "spot",
                "symbol": f"{symbol}USDT",
                "interval": "D",
                "start": start_timestamp,
                "end": end_timestamp,
                "limit": min(days, 200)
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(base_url, params=params)
                response.raise_for_status()

                data = response.json()

                if data.get("retCode") != 0:
                    logger.warning(f"Bybit API error for {symbol}: {data.get('retMsg')}")
                    return self._generate_synthetic_crypto_data_for_clustering(symbol, days)

                klines = data.get("result", {}).get("list", [])

                if not klines:
                    return self._generate_synthetic_crypto_data_for_clustering(symbol, days)

                # Обрабатываем данные и вычисляем статистики
                processed_data = []
                prices = []
                volumes = []

                for kline in klines:
                    price = float(kline[4])  # close price
                    volume = float(kline[5])
                    prices.append(price)
                    volumes.append(volume)

                # Вычисляем статистические показатели
                prices_array = np.array(prices)
                volumes_array = np.array(volumes)

                # Доходности
                returns = np.diff(prices_array) / prices_array[:-1]
                log_returns = np.diff(np.log(prices_array))

                # Статистики
                volatility_annualized = np.std(log_returns) * np.sqrt(252) if len(log_returns) > 0 else 0.0
                sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 0 and np.std(returns) > 0 else 0.0

                stats = {
                    'mean_price': self._clean_numeric_value(np.mean(prices_array)),
                    'std_price': self._clean_numeric_value(np.std(prices_array)),
                    'min_price': self._clean_numeric_value(np.min(prices_array)),
                    'max_price': self._clean_numeric_value(np.max(prices_array)),
                    'median_price': self._clean_numeric_value(np.median(prices_array)),
                    'mean_volume': self._clean_numeric_value(np.mean(volumes_array)),
                    'std_volume': self._clean_numeric_value(np.std(volumes_array)),
                    'mean_return': self._clean_numeric_value(np.mean(returns) if len(returns) > 0 else 0.0),
                    'std_return': self._clean_numeric_value(np.std(returns) if len(returns) > 0 else 0.0),
                    'skewness_return': self._calculate_skewness(returns),
                    'kurtosis_return': self._calculate_kurtosis(returns),
                    'volatility': self._clean_numeric_value(volatility_annualized),
                    'sharpe_ratio': self._clean_numeric_value(sharpe_ratio),
                    'price_range': self._clean_numeric_value(np.max(prices_array) - np.min(prices_array)),
                    'price_trend': self._clean_numeric_value((prices_array[-1] - prices_array[0]) / prices_array[0] if prices_array[0] != 0 else 0.0)
                }

                return pd.DataFrame([stats])

        except Exception as e:
            logger.error(f"Error fetching crypto data for {symbol}: {e}")
            return self._generate_synthetic_crypto_data_for_clustering(symbol, days)

    def _generate_synthetic_crypto_data_for_clustering(self, symbol: str, days: int) -> pd.DataFrame:
        """Генерация синтетических данных криптовалюты для кластеризации"""
        np.random.seed(hash(symbol) % 2**31)

        # Базовые цены для разных криптовалют
        base_prices = {
            'BTC': 45000, 'ETH': 2500, 'BNB': 350, 'ADA': 0.5, 'SOL': 100,
            'XRP': 0.6, 'DOT': 7, 'MATIC': 0.8, 'AVAX': 25, 'LINK': 12
        }

        base_price = base_prices.get(symbol, 100)

        # Генерируем временной ряд цен
        prices = []
        price = base_price

        for _ in range(days):
            change = np.random.normal(0, 0.02)
            price *= (1 + change)
            prices.append(price)

        prices_array = np.array(prices)
        volumes = np.random.lognormal(15, 1, days)

        # Вычисляем статистики
        returns = np.diff(prices_array) / prices_array[:-1]
        log_returns = np.diff(np.log(prices_array))

        volatility_annualized = np.std(log_returns) * np.sqrt(252) if len(log_returns) > 0 else 0.0
        sharpe_ratio = np.mean(returns) / np.std(returns) if len(returns) > 0 and np.std(returns) > 0 else 0.0

        stats = {
            'mean_price': self._clean_numeric_value(np.mean(prices_array)),
            'std_price': self._clean_numeric_value(np.std(prices_array)),
            'min_price': self._clean_numeric_value(np.min(prices_array)),
            'max_price': self._clean_numeric_value(np.max(prices_array)),
            'median_price': self._clean_numeric_value(np.median(prices_array)),
            'mean_volume': self._clean_numeric_value(np.mean(volumes)),
            'std_volume': self._clean_numeric_value(np.std(volumes)),
            'mean_return': self._clean_numeric_value(np.mean(returns) if len(returns) > 0 else 0.0),
            'std_return': self._clean_numeric_value(np.std(returns) if len(returns) > 0 else 0.0),
            'skewness_return': self._calculate_skewness(returns),
            'kurtosis_return': self._calculate_kurtosis(returns),
            'volatility': self._clean_numeric_value(volatility_annualized),
            'sharpe_ratio': self._clean_numeric_value(sharpe_ratio),
            'price_range': self._clean_numeric_value(np.max(prices_array) - np.min(prices_array)),
            'price_trend': self._clean_numeric_value((prices_array[-1] - prices_array[0]) / prices_array[0] if prices_array[0] != 0 else 0.0)
        }

        return pd.DataFrame([stats])

    async def _fetch_defi_data_for_clustering(self, protocol: str, days: int) -> pd.DataFrame:
        """Получение данных DeFi протокола для кластеризации"""
        try:
            # Ищем протокол в базе данных
            protocols = self.defi_repo.search_by_name(protocol, limit=1)
            if not protocols:
                return self._generate_synthetic_defi_data_for_clustering(protocol, days)

            protocol_obj = protocols[0]

            # Получаем историю TVL
            tvl_history = self.tvl_repo.find_by_protocol_id(protocol_obj.id, days=days)
            if not tvl_history or len(tvl_history) < 10:
                return self._generate_synthetic_defi_data_for_clustering(protocol, days)

            # Обрабатываем данные
            tvl_values = [float(record.tvl) if record.tvl else 0 for record in tvl_history]
            tvl_array = np.array(tvl_values)

            if len(tvl_array) < 2:
                return self._generate_synthetic_defi_data_for_clustering(protocol, days)

            # Вычисляем статистики
            tvl_returns = np.diff(tvl_array) / tvl_array[:-1]
            log_tvl = np.log(tvl_array + 1)  # +1 to avoid log(0)

            stats = {
                'mean_tvl': self._clean_numeric_value(np.mean(tvl_array)),
                'std_tvl': self._clean_numeric_value(np.std(tvl_array)),
                'min_tvl': self._clean_numeric_value(np.min(tvl_array)),
                'max_tvl': self._clean_numeric_value(np.max(tvl_array)),
                'median_tvl': self._clean_numeric_value(np.median(tvl_array)),
                'mean_return': self._clean_numeric_value(np.mean(tvl_returns) if len(tvl_returns) > 0 else 0.0),
                'std_return': self._clean_numeric_value(np.std(tvl_returns) if len(tvl_returns) > 0 else 0.0),
                'skewness_return': self._calculate_skewness(tvl_returns),
                'kurtosis_return': self._calculate_kurtosis(tvl_returns),
                'tvl_range': self._clean_numeric_value(np.max(tvl_array) - np.min(tvl_array)),
                'tvl_trend': self._clean_numeric_value((tvl_array[-1] - tvl_array[0]) / tvl_array[0] if tvl_array[0] > 0 else 0.0),
                'volatility': self._clean_numeric_value(np.std(tvl_returns) if len(tvl_returns) > 0 else 0.0),
                'log_tvl_mean': self._clean_numeric_value(np.mean(log_tvl)),
                'log_tvl_std': self._clean_numeric_value(np.std(log_tvl)),
                'growth_rate': self._clean_numeric_value(np.mean(tvl_returns) if len(tvl_returns) > 0 else 0.0)
            }

            return pd.DataFrame([stats])

        except Exception as e:
            logger.error(f"Error fetching DeFi data for {protocol}: {e}")
            return self._generate_synthetic_defi_data_for_clustering(protocol, days)

    def _generate_synthetic_defi_data_for_clustering(self, protocol: str, days: int) -> pd.DataFrame:
        """Генерация синтетических данных DeFi протокола для кластеризации"""
        np.random.seed(hash(protocol) % 2**31)

        base_tvls = {
            'Uniswap': 3500e6, 'Aave': 2800e6, 'Compound': 1200e6,
            'MakerDAO': 5000e6, 'Curve': 1800e6, 'SushiSwap': 800e6,
            'PancakeSwap': 2200e6, 'Balancer': 900e6, 'Yearn': 600e6, 'dYdX': 400e6
        }

        base_tvl = base_tvls.get(protocol, 1000e6)

        # Генерируем временной ряд TVL
        tvl_values = []
        tvl = base_tvl

        for _ in range(days):
            change = np.random.normal(0, 0.03)
            tvl *= (1 + change)
            tvl_values.append(max(tvl, 0))

        tvl_array = np.array(tvl_values)
        tvl_returns = np.diff(tvl_array) / tvl_array[:-1]
        log_tvl = np.log(tvl_array + 1)

        stats = {
            'mean_tvl': self._clean_numeric_value(np.mean(tvl_array)),
            'std_tvl': self._clean_numeric_value(np.std(tvl_array)),
            'min_tvl': self._clean_numeric_value(np.min(tvl_array)),
            'max_tvl': self._clean_numeric_value(np.max(tvl_array)),
            'median_tvl': self._clean_numeric_value(np.median(tvl_array)),
            'mean_return': self._clean_numeric_value(np.mean(tvl_returns) if len(tvl_returns) > 0 else 0.0),
            'std_return': self._clean_numeric_value(np.std(tvl_returns) if len(tvl_returns) > 0 else 0.0),
            'skewness_return': self._calculate_skewness(tvl_returns),
            'kurtosis_return': self._calculate_kurtosis(tvl_returns),
            'tvl_range': self._clean_numeric_value(np.max(tvl_array) - np.min(tvl_array)),
            'tvl_trend': self._clean_numeric_value((tvl_array[-1] - tvl_array[0]) / tvl_array[0] if tvl_array[0] != 0 else 0.0),
            'volatility': self._clean_numeric_value(np.std(tvl_returns) if len(tvl_returns) > 0 else 0.0),
            'log_tvl_mean': self._clean_numeric_value(np.mean(log_tvl)),
            'log_tvl_std': self._clean_numeric_value(np.std(log_tvl)),
            'growth_rate': self._clean_numeric_value(np.mean(tvl_returns) if len(tvl_returns) > 0 else 0.0)
        }

        return pd.DataFrame([stats])

    def _calculate_skewness(self, data: np.array) -> float:
        """Вычисление коэффициента асимметрии"""
        if len(data) < 3:
            return 0.0
        n = len(data)
        mean = np.mean(data)
        std = np.std(data)
        if std == 0 or np.isnan(std) or np.isnan(mean):
            return 0.0
        skew = (n / ((n-1) * (n-2))) * np.sum(((data - mean) / std) ** 3)
        return 0.0 if np.isnan(skew) or np.isinf(skew) else float(skew)

    def _calculate_kurtosis(self, data: np.array) -> float:
        """Вычисление коэффициента эксцесса"""
        if len(data) < 4:
            return 0.0
        n = len(data)
        mean = np.mean(data)
        std = np.std(data)
        if std == 0 or np.isnan(std) or np.isnan(mean):
            return 0.0
        kurt = (n * (n+1) / ((n-1) * (n-2) * (n-3))) * np.sum(((data - mean) / std) ** 4)
        result = kurt - 3 * (n-1)**2 / ((n-2) * (n-3))
        return 0.0 if np.isnan(result) or np.isinf(result) else float(result)

    def _clean_numeric_value(self, value) -> float:
        """Очистка числового значения от NaN и Inf"""
        if np.isnan(value) or np.isinf(value):
            return 0.0
        return float(value)

    async def get_kmeans_clustering_data(
        self,
        data_type: str = "crypto",
        symbols: str = "BTC,ETH,BNB,ADA,SOL",
        days: int = 30,
        n_clusters: int = 3,
        features: str = "mean_price,std_price,volatility,mean_return"
    ) -> JSONResponse:
        """API для K-means кластеризации"""
        try:
            symbol_list = [s.strip() for s in symbols.split(',')]
            feature_list = [f.strip() for f in features.split(',')]

            # Получаем данные
            df = await self._get_clustering_data(data_type, symbol_list, days)

            if df.empty:
                return JSONResponse({
                    "success": False,
                    "error": "Данные не найдены"
                })

            # Выбираем признаки для кластеризации
            available_features = [col for col in feature_list if col in df.columns]
            if not available_features:
                return JSONResponse({
                    "success": False,
                    "error": f"Признаки {feature_list} не найдены в данных"
                })

            X = df[available_features].values

            # Стандартизируем данные
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # K-means кластеризация
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)

            # Метрики качества
            silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(X_scaled, cluster_labels)
            davies_bouldin = davies_bouldin_score(X_scaled, cluster_labels)

            # PCA для визуализации
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)

            # Создаем визуализацию
            fig = self._create_kmeans_plot(X_pca, cluster_labels, df['symbol'].tolist(), kmeans, X_scaled)

            # Анализ кластеров
            cluster_analysis = self._analyze_clusters(df, cluster_labels, available_features)

            return JSONResponse({
                "success": True,
                "data": {
                    "clusters": cluster_labels.tolist(),
                    "symbols": df['symbol'].tolist(),
                    "features": available_features,
                    "metrics": {
                        "silhouette_score": float(silhouette_avg),
                        "calinski_harabasz_score": float(calinski_harabasz),
                        "davies_bouldin_score": float(davies_bouldin),
                        "inertia": float(kmeans.inertia_)
                    },
                    "cluster_centers": kmeans.cluster_centers_.tolist(),
                    "plot": fig.to_json(),
                    "cluster_analysis": cluster_analysis,
                    "pca_explained_variance": pca.explained_variance_ratio_.tolist()
                }
            })

        except Exception as e:
            logger.error(f"Error in K-means clustering: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка кластеризации: {str(e)}"
            })

    def _create_kmeans_plot(self, X_pca, cluster_labels, symbols, kmeans, X_scaled):
        """Создание графика K-means кластеризации"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Результаты кластеризации (PCA)', 'Центры кластеров'),
            specs=[[{"type": "scatter"}, {"type": "bar"}]]
        )

        # График кластеров в пространстве PCA
        colors = px.colors.qualitative.Set1
        unique_clusters = np.unique(cluster_labels)

        for i, cluster in enumerate(unique_clusters):
            mask = cluster_labels == cluster
            cluster_symbols = [symbols[j] for j in range(len(symbols)) if mask[j]]

            fig.add_trace(
                go.Scatter(
                    x=X_pca[mask, 0],
                    y=X_pca[mask, 1],
                    mode='markers+text',
                    text=cluster_symbols,
                    textposition='top center',
                    name=f'Кластер {cluster}',
                    marker=dict(
                        color=colors[i % len(colors)],
                        size=12,
                        line=dict(width=2, color='white')
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        # График центров кластеров
        if len(kmeans.cluster_centers_) > 0 and len(kmeans.cluster_centers_[0]) > 0:
            for i, center in enumerate(kmeans.cluster_centers_):
                fig.add_trace(
                    go.Bar(
                        x=[f'Признак {j+1}' for j in range(len(center))],
                        y=center,
                        name=f'Центр кластера {i}',
                        marker_color=colors[i % len(colors)],
                        showlegend=False
                    ),
                    row=1, col=2
                )

        fig.update_layout(
            title='K-means кластеризация данных',
            height=500,
            template='plotly_white'
        )

        fig.update_xaxes(title_text="Первая главная компонента", row=1, col=1)
        fig.update_yaxes(title_text="Вторая главная компонента", row=1, col=1)
        fig.update_xaxes(title_text="Признаки", row=1, col=2)
        fig.update_yaxes(title_text="Значения центров", row=1, col=2)

        return fig

    def _analyze_clusters(self, df, cluster_labels, features):
        """Анализ характеристик кластеров"""
        analysis = {}

        for cluster_id in np.unique(cluster_labels):
            cluster_mask = cluster_labels == cluster_id
            cluster_data = df[cluster_mask]

            cluster_stats = {}
            for feature in features:
                if feature in cluster_data.columns:
                    cluster_stats[feature] = {
                        'mean': self._clean_numeric_value(cluster_data[feature].mean()),
                        'std': self._clean_numeric_value(cluster_data[feature].std()),
                        'min': self._clean_numeric_value(cluster_data[feature].min()),
                        'max': self._clean_numeric_value(cluster_data[feature].max())
                    }

            analysis[f'cluster_{cluster_id}'] = {
                'size': int(np.sum(cluster_mask)),
                'symbols': cluster_data['symbol'].tolist(),
                'statistics': cluster_stats
            }

        return analysis

    async def get_dbscan_clustering_data(
        self,
        data_type: str = "crypto",
        symbols: str = "BTC,ETH,BNB,ADA,SOL",
        days: int = 30,
        eps: float = 0.5,
        min_samples: int = 2,
        features: str = "mean_price,std_price,volatility,mean_return"
    ) -> JSONResponse:
        """API для DBSCAN кластеризации"""
        try:
            symbol_list = [s.strip() for s in symbols.split(',')]
            feature_list = [f.strip() for f in features.split(',')]

            # Получаем данные
            df = await self._get_clustering_data(data_type, symbol_list, days)

            if df.empty:
                return JSONResponse({
                    "success": False,
                    "error": "Данные не найдены"
                })

            # Выбираем признаки для кластеризации
            available_features = [col for col in feature_list if col in df.columns]
            if not available_features:
                return JSONResponse({
                    "success": False,
                    "error": f"Признаки {feature_list} не найдены в данных"
                })

            X = df[available_features].values

            # Стандартизируем данные
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # DBSCAN кластеризация
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            cluster_labels = dbscan.fit_predict(X_scaled)

            # Подсчет кластеров и выбросов
            n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            n_noise = list(cluster_labels).count(-1)

            # Метрики качества (только если есть кластеры)
            metrics = {}
            if n_clusters > 1:
                # Исключаем выбросы для расчета метрик
                mask = cluster_labels != -1
                if np.sum(mask) > 1:
                    try:
                        silhouette_avg = silhouette_score(X_scaled[mask], cluster_labels[mask])
                        calinski_harabasz = calinski_harabasz_score(X_scaled[mask], cluster_labels[mask])
                        davies_bouldin = davies_bouldin_score(X_scaled[mask], cluster_labels[mask])

                        metrics = {
                            "silhouette_score": float(silhouette_avg),
                            "calinski_harabasz_score": float(calinski_harabasz),
                            "davies_bouldin_score": float(davies_bouldin),
                            "n_clusters": n_clusters,
                            "n_noise": n_noise
                        }
                    except:
                        metrics = {
                            "n_clusters": n_clusters,
                            "n_noise": n_noise,
                            "error": "Невозможно вычислить метрики качества"
                        }
                else:
                    metrics = {
                        "n_clusters": n_clusters,
                        "n_noise": n_noise,
                        "error": "Недостаточно данных для расчета метрик"
                    }
            else:
                metrics = {
                    "n_clusters": n_clusters,
                    "n_noise": n_noise,
                    "error": "Кластеры не найдены"
                }

            # PCA для визуализации
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)

            # Создаем визуализацию
            fig = self._create_dbscan_plot(X_pca, cluster_labels, df['symbol'].tolist())

            # Анализ кластеров
            cluster_analysis = self._analyze_clusters(df, cluster_labels, available_features)

            return JSONResponse({
                "success": True,
                "data": {
                    "clusters": cluster_labels.tolist(),
                    "symbols": df['symbol'].tolist(),
                    "features": available_features,
                    "metrics": metrics,
                    "plot": fig.to_json(),
                    "cluster_analysis": cluster_analysis,
                    "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
                    "eps": eps,
                    "min_samples": min_samples
                }
            })

        except Exception as e:
            logger.error(f"Error in DBSCAN clustering: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка кластеризации: {str(e)}"
            })

    def _create_dbscan_plot(self, X_pca, cluster_labels, symbols):
        """Создание графика DBSCAN кластеризации"""
        fig = go.Figure()

        # Цвета для кластеров
        colors = px.colors.qualitative.Set1
        unique_clusters = np.unique(cluster_labels)

        for cluster in unique_clusters:
            mask = cluster_labels == cluster
            cluster_symbols = [symbols[i] for i in range(len(symbols)) if mask[i]]

            if cluster == -1:
                # Выбросы
                fig.add_trace(
                    go.Scatter(
                        x=X_pca[mask, 0],
                        y=X_pca[mask, 1],
                        mode='markers+text',
                        text=cluster_symbols,
                        textposition='top center',
                        name='Выбросы',
                        marker=dict(
                            color='black',
                            size=10,
                            symbol='x',
                            line=dict(width=2, color='white')
                        )
                    )
                )
            else:
                # Обычные кластеры
                color_idx = cluster % len(colors)
                fig.add_trace(
                    go.Scatter(
                        x=X_pca[mask, 0],
                        y=X_pca[mask, 1],
                        mode='markers+text',
                        text=cluster_symbols,
                        textposition='top center',
                        name=f'Кластер {cluster}',
                        marker=dict(
                            color=colors[color_idx],
                            size=12,
                            line=dict(width=2, color='white')
                        )
                    )
                )

        fig.update_layout(
            title='DBSCAN кластеризация данных',
            xaxis_title="Первая главная компонента",
            yaxis_title="Вторая главная компонента",
            template='plotly_white',
            height=500
        )

        return fig

    async def get_hierarchical_clustering_data(
        self,
        data_type: str = "crypto",
        symbols: str = "BTC,ETH,BNB,ADA,SOL",
        days: int = 30,
        n_clusters: int = 3,
        linkage: str = "ward",
        features: str = "mean_price,std_price,volatility,mean_return"
    ) -> JSONResponse:
        """API для иерархической кластеризации"""
        try:
            symbol_list = [s.strip() for s in symbols.split(',')]
            feature_list = [f.strip() for f in features.split(',')]

            # Получаем данные
            df = await self._get_clustering_data(data_type, symbol_list, days)

            if df.empty:
                return JSONResponse({
                    "success": False,
                    "error": "Данные не найдены"
                })

            # Выбираем признаки для кластеризации
            available_features = [col for col in feature_list if col in df.columns]
            if not available_features:
                return JSONResponse({
                    "success": False,
                    "error": f"Признаки {feature_list} не найдены в данных"
                })

            X = df[available_features].values

            # Стандартизируем данные
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Иерархическая кластеризация
            hierarchical = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage=linkage
            )
            cluster_labels = hierarchical.fit_predict(X_scaled)

            # Метрики качества
            silhouette_avg = silhouette_score(X_scaled, cluster_labels)
            calinski_harabasz = calinski_harabasz_score(X_scaled, cluster_labels)
            davies_bouldin = davies_bouldin_score(X_scaled, cluster_labels)

            # PCA для визуализации
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)

            # Создаем визуализацию
            fig = self._create_hierarchical_plot(X_pca, cluster_labels, df['symbol'].tolist())

            # Создаем дендрограмму
            try:
                dendrogram_fig = self._create_dendrogram(X_scaled, df['symbol'].tolist(), linkage)
            except Exception as dendrogram_error:
                logger.error(f"Error creating dendrogram: {dendrogram_error}")
                # Создаем простую заглушку вместо дендрограммы
                import plotly.graph_objects as go
                dendrogram_fig = go.Figure()
                dendrogram_fig.add_annotation(
                    text="Дендрограмма недоступна",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False
                )
                dendrogram_fig.update_layout(
                    title='Дендрограмма недоступна',
                    template='plotly_white',
                    height=400
                )

            # Анализ кластеров
            cluster_analysis = self._analyze_clusters(df, cluster_labels, available_features)

            return JSONResponse({
                "success": True,
                "data": {
                    "clusters": cluster_labels.tolist(),
                    "symbols": df['symbol'].tolist(),
                    "features": available_features,
                    "metrics": {
                        "silhouette_score": float(silhouette_avg),
                        "calinski_harabasz_score": float(calinski_harabasz),
                        "davies_bouldin_score": float(davies_bouldin)
                    },
                    "plot": fig.to_json(),
                    "dendrogram": dendrogram_fig.to_json(),
                    "cluster_analysis": cluster_analysis,
                    "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
                    "linkage": linkage
                }
            })

        except Exception as e:
            logger.error(f"Error in hierarchical clustering: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка кластеризации: {str(e)}"
            })

    def _create_hierarchical_plot(self, X_pca, cluster_labels, symbols):
        """Создание графика иерархической кластеризации"""
        fig = go.Figure()

        colors = px.colors.qualitative.Set1
        unique_clusters = np.unique(cluster_labels)

        for i, cluster in enumerate(unique_clusters):
            mask = cluster_labels == cluster
            cluster_symbols = [symbols[j] for j in range(len(symbols)) if mask[j]]

            fig.add_trace(
                go.Scatter(
                    x=X_pca[mask, 0],
                    y=X_pca[mask, 1],
                    mode='markers+text',
                    text=cluster_symbols,
                    textposition='top center',
                    name=f'Кластер {cluster}',
                    marker=dict(
                        color=colors[i % len(colors)],
                        size=12,
                        line=dict(width=2, color='white')
                    )
                )
            )

        fig.update_layout(
            title='Иерархическая кластеризация данных',
            xaxis_title="Первая главная компонента",
            yaxis_title="Вторая главная компонента",
            template='plotly_white',
            height=500
        )

        return fig

    def _create_dendrogram(self, X_scaled, symbols, linkage_method):
        """Создание дендрограммы"""
        try:
            from scipy.cluster.hierarchy import dendrogram, linkage
            import plotly.graph_objects as go
            import numpy as np

            # Вычисляем linkage matrix
            linkage_matrix = linkage(X_scaled, method=linkage_method)

            # Используем scipy для получения координат дендрограммы
            dendro_data = dendrogram(
                linkage_matrix,
                labels=symbols,
                no_plot=True  # Не рисуем matplotlib график, просто получаем данные
            )

            # Создаем plotly график из данных дендрограммы
            fig = go.Figure()

            # Добавляем линии дендрограммы
            for i in range(len(dendro_data['icoord'])):
                x_coords = dendro_data['icoord'][i]
                y_coords = dendro_data['dcoord'][i]

                fig.add_trace(go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode='lines',
                    line=dict(color='blue', width=2),
                    showlegend=False,
                    hoverinfo='none'
                ))

            # Добавляем подписи листьев (символов)
            leaf_labels = dendro_data['ivl']  # Labels в правильном порядке
            leaf_positions = np.arange(5, len(leaf_labels) * 10 + 5, 10)

            for i, (label, pos) in enumerate(zip(leaf_labels, leaf_positions)):
                fig.add_annotation(
                    x=pos,
                    y=-0.02 * max(dendro_data['dcoord'][0]),  # Небольшой отступ вниз
                    text=label,
                    showarrow=False,
                    textangle=-45,
                    font=dict(size=10),
                    xanchor='right'
                )

            # Настраиваем layout
            fig.update_layout(
                title=f'Дендрограмма иерархической кластеризации (метод: {linkage_method})',
                xaxis_title="Образцы",
                yaxis_title="Расстояние",
                template='plotly_white',
                height=400,
                showlegend=False,
                xaxis=dict(
                    showticklabels=False,  # Скрываем стандартные подписи оси X
                    range=[0, len(symbols) * 10]
                ),
                yaxis=dict(
                    range=[min(min(coord) for coord in dendro_data['dcoord']) * 1.1,
                           max(max(coord) for coord in dendro_data['dcoord']) * 1.1]
                )
            )

            return fig

        except ImportError:
            logger.error("scipy not available for dendrogram creation")
            return self._create_fallback_dendrogram(symbols, linkage_method, "scipy не установлен")

        except Exception as e:
            logger.error(f"Error creating dendrogram: {e}")
            return self._create_fallback_dendrogram(symbols, linkage_method, str(e))

    def _create_fallback_dendrogram(self, symbols, linkage_method, error_msg):
        """Создание fallback дендрограммы в случае ошибки"""
        import plotly.graph_objects as go

        fig = go.Figure()

        # Создаем простую иерархическую структуру для демонстрации
        fig.add_annotation(
            text=f"Дендрограмма недоступна: {error_msg}<br><br>Анализируемые активы: {', '.join(symbols)}<br>Метод связи: {linkage_method}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=12, color="red")
        )

        fig.update_layout(
            title='Дендрограмма недоступна',
            template='plotly_white',
            height=400
        )

        return fig

    async def get_clustering_comparison_data(
        self,
        data_type: str = "crypto",
        symbols: str = "BTC,ETH,BNB,ADA,SOL",
        days: int = 30,
        features: str = "mean_price,std_price,volatility,mean_return"
    ) -> JSONResponse:
        """API для сравнения методов кластеризации"""
        try:
            symbol_list = [s.strip() for s in symbols.split(',')]
            feature_list = [f.strip() for f in features.split(',')]

            # Получаем данные
            df = await self._get_clustering_data(data_type, symbol_list, days)

            if df.empty:
                return JSONResponse({
                    "success": False,
                    "error": "Данные не найдены"
                })

            # Выбираем признаки для кластеризации
            available_features = [col for col in feature_list if col in df.columns]
            if not available_features:
                return JSONResponse({
                    "success": False,
                    "error": f"Признаки {feature_list} не найдены в данных"
                })

            X = df[available_features].values
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # PCA для визуализации
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)

            # Применяем разные методы кластеризации
            methods_results = {}

            # K-means с разным количеством кластеров
            for n_clusters in [2, 3, 4]:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X_scaled)

                silhouette_avg = silhouette_score(X_scaled, labels)
                methods_results[f'kmeans_{n_clusters}'] = {
                    'labels': labels.tolist(),
                    'method': 'K-means',
                    'params': f'k={n_clusters}',
                    'silhouette_score': float(silhouette_avg),
                    'n_clusters': n_clusters
                }

            # DBSCAN с разными параметрами
            for eps in [0.3, 0.5, 0.7]:
                dbscan = DBSCAN(eps=eps, min_samples=2)
                labels = dbscan.fit_predict(X_scaled)
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                n_noise = list(labels).count(-1)

                if n_clusters > 1:
                    mask = labels != -1
                    if np.sum(mask) > 1:
                        try:
                            silhouette_avg = silhouette_score(X_scaled[mask], labels[mask])
                        except:
                            silhouette_avg = -1
                    else:
                        silhouette_avg = -1
                else:
                    silhouette_avg = -1

                methods_results[f'dbscan_{eps}'] = {
                    'labels': labels.tolist(),
                    'method': 'DBSCAN',
                    'params': f'eps={eps}',
                    'silhouette_score': float(silhouette_avg),
                    'n_clusters': n_clusters,
                    'n_noise': n_noise
                }

            # Иерархическая кластеризация
            for n_clusters in [2, 3, 4]:
                hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
                labels = hierarchical.fit_predict(X_scaled)

                silhouette_avg = silhouette_score(X_scaled, labels)
                methods_results[f'hierarchical_{n_clusters}'] = {
                    'labels': labels.tolist(),
                    'method': 'Hierarchical',
                    'params': f'k={n_clusters}',
                    'silhouette_score': float(silhouette_avg),
                    'n_clusters': n_clusters
                }

            # Создаем сравнительную визуализацию
            comparison_fig = self._create_comparison_plot(X_pca, methods_results, symbol_list)

            return JSONResponse({
                "success": True,
                "data": {
                    "symbols": df['symbol'].tolist(),
                    "features": available_features,
                    "methods_results": methods_results,
                    "comparison_plot": comparison_fig.to_json(),
                    "pca_explained_variance": pca.explained_variance_ratio_.tolist()
                }
            })

        except Exception as e:
            logger.error(f"Error in clustering comparison: {e}")
            return JSONResponse({
                "success": False,
                "error": f"Ошибка сравнения: {str(e)}"
            })

    def _create_comparison_plot(self, X_pca, methods_results, symbols):
        """Создание сравнительного графика методов кластеризации"""
        from plotly.subplots import make_subplots

        # Выбираем лучшие результаты для каждого метода
        best_methods = {}
        for key, result in methods_results.items():
            method = result['method']
            if method not in best_methods or result['silhouette_score'] > best_methods[method]['silhouette_score']:
                best_methods[method] = result
                best_methods[method]['key'] = key

        n_methods = len(best_methods)
        cols = min(3, n_methods)
        rows = (n_methods + cols - 1) // cols

        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[f"{method} ({data['params']})" for method, data in best_methods.items()],
            specs=[[{"type": "scatter"}] * cols for _ in range(rows)]
        )

        colors = px.colors.qualitative.Set1

        for idx, (method, data) in enumerate(best_methods.items()):
            row = idx // cols + 1
            col = idx % cols + 1

            labels = np.array(data['labels'])
            unique_labels = np.unique(labels)

            for i, label in enumerate(unique_labels):
                mask = labels == label
                mask_indices = np.where(mask)[0]
                cluster_symbols = [symbols[j] for j in mask_indices if j < len(symbols)]

                if label == -1:  # Выбросы для DBSCAN
                    color = 'black'
                    name = 'Выбросы'
                    symbol = 'x'
                else:
                    color = colors[i % len(colors)]
                    name = f'Кластер {label}'
                    symbol = 'circle'

                fig.add_trace(
                    go.Scatter(
                        x=X_pca[mask, 0],
                        y=X_pca[mask, 1],
                        mode='markers+text',
                        text=cluster_symbols,
                        textposition='top center',
                        name=f'{method}: {name}',
                        marker=dict(
                            color=color,
                            size=10,
                            symbol=symbol,
                            line=dict(width=1, color='white')
                        ),
                        showlegend=False
                    ),
                    row=row, col=col
                )

        fig.update_layout(
            title='Сравнение методов кластеризации',
            height=300 * rows,
            template='plotly_white'
        )

        return fig


def create_lab4_router() -> APIRouter:
    """Создание роутера для Лабораторной работы №4"""
    router = APIRouter(prefix="/lab4", tags=["lab4"])
    controller = Lab4Controller()

    # Веб-страницы
    @router.get("/", response_class=HTMLResponse)
    async def lab4_main_page(request: Request):
        return await controller.lab4_page(request)

    @router.get("/kmeans", response_class=HTMLResponse)
    async def kmeans_clustering_page(request: Request):
        return await controller.kmeans_clustering_page(request)

    @router.get("/dbscan", response_class=HTMLResponse)
    async def dbscan_clustering_page(request: Request):
        return await controller.dbscan_clustering_page(request)

    @router.get("/hierarchical", response_class=HTMLResponse)
    async def hierarchical_clustering_page(request: Request):
        return await controller.hierarchical_clustering_page(request)

    @router.get("/comparison", response_class=HTMLResponse)
    async def clustering_comparison_page(request: Request):
        return await controller.clustering_comparison_page(request)

    # API эндпоинты
    @router.get("/api/kmeans-clustering")
    async def kmeans_clustering_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbols: str = Query("BTC,ETH,BNB,ADA,SOL", description="Символы через запятую"),
        days: int = Query(30, ge=10, le=365, description="Количество дней для анализа"),
        n_clusters: int = Query(3, ge=2, le=10, description="Количество кластеров"),
        features: str = Query("mean_price,std_price,volatility,mean_return", description="Признаки через запятую")
    ):
        return await controller.get_kmeans_clustering_data(
            data_type, symbols, days, n_clusters, features
        )

    @router.get("/api/dbscan-clustering")
    async def dbscan_clustering_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbols: str = Query("BTC,ETH,BNB,ADA,SOL", description="Символы через запятую"),
        days: int = Query(30, ge=10, le=365, description="Количество дней для анализа"),
        eps: float = Query(0.5, ge=0.1, le=2.0, description="Параметр eps"),
        min_samples: int = Query(2, ge=1, le=10, description="Минимальное количество образцов"),
        features: str = Query("mean_price,std_price,volatility,mean_return", description="Признаки через запятую")
    ):
        return await controller.get_dbscan_clustering_data(
            data_type, symbols, days, eps, min_samples, features
        )

    @router.get("/api/hierarchical-clustering")
    async def hierarchical_clustering_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbols: str = Query("BTC,ETH,BNB,ADA,SOL", description="Символы через запятую"),
        days: int = Query(30, ge=10, le=365, description="Количество дней для анализа"),
        n_clusters: int = Query(3, ge=2, le=10, description="Количество кластеров"),
        linkage: str = Query("ward", description="Метод связи: ward, complete, average, single"),
        features: str = Query("mean_price,std_price,volatility,mean_return", description="Признаки через запятую")
    ):
        return await controller.get_hierarchical_clustering_data(
            data_type, symbols, days, n_clusters, linkage, features
        )

    @router.get("/api/clustering-comparison")
    async def clustering_comparison_api(
        data_type: str = Query("crypto", description="Тип данных: crypto или defi"),
        symbols: str = Query("BTC,ETH,BNB,ADA,SOL", description="Символы через запятую"),
        days: int = Query(30, ge=10, le=365, description="Количество дней для анализа"),
        features: str = Query("mean_price,std_price,volatility,mean_return", description="Признаки через запятую")
    ):
        return await controller.get_clustering_comparison_data(
            data_type, symbols, days, features
        )

    return router