import numpy as np
import pandas as pd
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from scipy.optimize import curve_fit
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class Lab3ApproximationService:
    """Сервис для полиномиальной аппроксимации и прогнозирования"""

    def __init__(self):
        self.models = {}

    async def create_forecast(
        self,
        df: pd.DataFrame,
        field: str,
        method: str,
        forecast_days: int
    ) -> Dict[str, Any]:
        """Создание прогноза различными методами"""
        try:
            forecasts = {}
            confidence_intervals = {}
            metrics = {}

            # Подготовка данных
            values = df[field].values
            time_indices = np.arange(len(values))

            if method == "polynomial" or method == "all":
                # Полиномиальное прогнозирование для разных степеней
                for degree in [1, 2, 3, 4, 5]:
                    forecast, confidence, metric = self._polynomial_forecast(
                        time_indices, values, degree, forecast_days
                    )
                    forecasts[f'polynomial_degree_{degree}'] = forecast
                    confidence_intervals[f'polynomial_degree_{degree}'] = confidence
                    metrics[f'polynomial_degree_{degree}'] = metric

            if method == "linear" or method == "all":
                # Линейное прогнозирование
                forecast, confidence, metric = self._linear_forecast(
                    time_indices, values, forecast_days
                )
                forecasts['linear'] = forecast
                confidence_intervals['linear'] = confidence
                metrics['linear'] = metric

            if method == "exponential" or method == "all":
                # Экспоненциальное прогнозирование
                forecast, confidence, metric = self._exponential_forecast(
                    time_indices, values, forecast_days
                )
                forecasts['exponential'] = forecast
                confidence_intervals['exponential'] = confidence
                metrics['exponential'] = metric

            if method == "moving_average" or method == "all":
                # Скользящее среднее
                forecast, confidence, metric = self._moving_average_forecast(
                    values, forecast_days
                )
                forecasts['moving_average'] = forecast
                confidence_intervals['moving_average'] = confidence
                metrics['moving_average'] = metric

            return {
                "success": True,
                "forecasts": forecasts,
                "confidence_intervals": confidence_intervals,
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Error in forecast creation: {e}")
            return {
                "success": False,
                "error": f"Ошибка создания прогноза: {str(e)}"
            }

    def _polynomial_forecast(
        self,
        time_indices: np.ndarray,
        values: np.ndarray,
        degree: int,
        forecast_days: int
    ) -> Tuple[List[float], Dict[str, List[float]], Dict[str, float]]:
        """Полиномиальное прогнозирование"""
        try:
            # Создание полиномиальных признаков
            poly_features = PolynomialFeatures(degree=degree)
            X_poly = poly_features.fit_transform(time_indices.reshape(-1, 1))

            # Обучение модели
            model = LinearRegression()
            model.fit(X_poly, values)

            # Прогноз на исторических данных для оценки качества
            y_pred = model.predict(X_poly)

            # Метрики качества
            r2 = r2_score(values, y_pred)
            mse = mean_squared_error(values, y_pred)
            rmse = np.sqrt(mse)

            # Прогноз на будущее
            future_indices = np.arange(len(time_indices), len(time_indices) + forecast_days)
            future_X_poly = poly_features.transform(future_indices.reshape(-1, 1))
            forecast = model.predict(future_X_poly)

            # Доверительные интервалы (упрощенный расчет)
            residuals = values - y_pred
            std_residual = np.std(residuals)

            confidence_lower = forecast - 1.96 * std_residual
            confidence_upper = forecast + 1.96 * std_residual

            confidence_intervals = {
                'lower': confidence_lower.tolist(),
                'upper': confidence_upper.tolist()
            }

            metrics = {
                'r2': float(r2),
                'mse': float(mse),
                'rmse': float(rmse),
                'degree': degree
            }

            return forecast.tolist(), confidence_intervals, metrics

        except Exception as e:
            logger.error(f"Error in polynomial forecast: {e}")
            return [], {}, {}

    def _linear_forecast(
        self,
        time_indices: np.ndarray,
        values: np.ndarray,
        forecast_days: int
    ) -> Tuple[List[float], Dict[str, List[float]], Dict[str, float]]:
        """Линейное прогнозирование"""
        try:
            # Простая линейная регрессия
            X = time_indices.reshape(-1, 1)
            model = LinearRegression()
            model.fit(X, values)

            # Прогноз на исторических данных
            y_pred = model.predict(X)

            # Метрики
            r2 = r2_score(values, y_pred)
            mse = mean_squared_error(values, y_pred)
            rmse = np.sqrt(mse)

            # Прогноз на будущее
            future_indices = np.arange(len(time_indices), len(time_indices) + forecast_days)
            forecast = model.predict(future_indices.reshape(-1, 1))

            # Доверительные интервалы
            residuals = values - y_pred
            std_residual = np.std(residuals)

            confidence_lower = forecast - 1.96 * std_residual
            confidence_upper = forecast + 1.96 * std_residual

            confidence_intervals = {
                'lower': confidence_lower.tolist(),
                'upper': confidence_upper.tolist()
            }

            metrics = {
                'r2': float(r2),
                'mse': float(mse),
                'rmse': float(rmse),
                'slope': float(model.coef_[0]),
                'intercept': float(model.intercept_)
            }

            return forecast.tolist(), confidence_intervals, metrics

        except Exception as e:
            logger.error(f"Error in linear forecast: {e}")
            return [], {}, {}

    def _exponential_forecast(
        self,
        time_indices: np.ndarray,
        values: np.ndarray,
        forecast_days: int
    ) -> Tuple[List[float], Dict[str, List[float]], Dict[str, float]]:
        """Экспоненциальное прогнозирование"""
        try:
            # Определяем экспоненциальную функцию
            def exponential_func(x, a, b, c):
                return a * np.exp(b * x) + c

            # Пытаемся подогнать экспоненциальную функцию
            try:
                # Начальные параметры
                initial_guess = [values[0], 0.01, values.mean()]

                popt, pcov = curve_fit(
                    exponential_func,
                    time_indices,
                    values,
                    p0=initial_guess,
                    maxfev=5000
                )

                # Прогноз на исторических данных
                y_pred = exponential_func(time_indices, *popt)

                # Проверяем качество аппроксимации
                r2 = r2_score(values, y_pred)

                # Если аппроксимация плохая, используем линейную
                if r2 < 0 or np.any(np.isnan(y_pred)) or np.any(np.isinf(y_pred)):
                    return self._linear_forecast(time_indices, values, forecast_days)

                # Прогноз на будущее
                future_indices = np.arange(len(time_indices), len(time_indices) + forecast_days)
                forecast = exponential_func(future_indices, *popt)

                # Проверяем прогноз на разумность
                if np.any(np.isnan(forecast)) or np.any(np.isinf(forecast)) or np.any(forecast < 0):
                    return self._linear_forecast(time_indices, values, forecast_days)

                # Метрики
                mse = mean_squared_error(values, y_pred)
                rmse = np.sqrt(mse)

                # Доверительные интервалы (упрощенный расчет)
                residuals = values - y_pred
                std_residual = np.std(residuals)

                confidence_lower = forecast - 1.96 * std_residual
                confidence_upper = forecast + 1.96 * std_residual

                confidence_intervals = {
                    'lower': confidence_lower.tolist(),
                    'upper': confidence_upper.tolist()
                }

                metrics = {
                    'r2': float(r2),
                    'mse': float(mse),
                    'rmse': float(rmse),
                    'parameters': {
                        'a': float(popt[0]),
                        'b': float(popt[1]),
                        'c': float(popt[2])
                    }
                }

                return forecast.tolist(), confidence_intervals, metrics

            except Exception:
                # Если экспоненциальная аппроксимация не удалась, используем линейную
                return self._linear_forecast(time_indices, values, forecast_days)

        except Exception as e:
            logger.error(f"Error in exponential forecast: {e}")
            return [], {}, {}

    def _moving_average_forecast(
        self,
        values: np.ndarray,
        forecast_days: int,
        window: int = None
    ) -> Tuple[List[float], Dict[str, List[float]], Dict[str, float]]:
        """Прогнозирование на основе скользящего среднего"""
        try:
            if window is None:
                window = min(7, len(values) // 3)  # Адаптивный размер окна

            if window <= 0:
                window = min(3, len(values))

            # Вычисляем скользящее среднее
            moving_avg = pd.Series(values).rolling(window=window, min_periods=1).mean()

            # Последнее значение скользящего среднего как базовый прогноз
            last_avg = moving_avg.iloc[-1]

            # Тренд на основе последних значений
            if len(moving_avg) >= 2:
                trend = moving_avg.iloc[-1] - moving_avg.iloc[-2]
            else:
                trend = 0

            # Прогноз с учетом тренда
            forecast = []
            for i in range(forecast_days):
                forecast_value = last_avg + trend * (i + 1)
                forecast.append(forecast_value)

            # Оценка качества на исторических данных
            if len(values) > window:
                # Используем последние значения для оценки качества
                test_values = values[-window:]
                predicted_values = moving_avg.iloc[-window:].values

                r2 = r2_score(test_values, predicted_values)
                mse = mean_squared_error(test_values, predicted_values)
                rmse = np.sqrt(mse)
            else:
                r2 = 0.5  # Средняя оценка при недостатке данных
                mse = np.var(values)
                rmse = np.sqrt(mse)

            # Доверительные интервалы на основе исторической волатильности
            volatility = np.std(values[-window:]) if len(values) >= window else np.std(values)

            confidence_lower = [f - 1.96 * volatility for f in forecast]
            confidence_upper = [f + 1.96 * volatility for f in forecast]

            confidence_intervals = {
                'lower': confidence_lower,
                'upper': confidence_upper
            }

            metrics = {
                'r2': float(r2),
                'mse': float(mse),
                'rmse': float(rmse),
                'window': window,
                'trend': float(trend)
            }

            return forecast, confidence_intervals, metrics

        except Exception as e:
            logger.error(f"Error in moving average forecast: {e}")
            return [], {}, {}

    def calculate_model_comparison(self, metrics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Сравнение качества различных моделей"""
        try:
            comparison = {
                'best_r2': {'model': '', 'value': -float('inf')},
                'best_rmse': {'model': '', 'value': float('inf')},
                'ranking': []
            }

            model_scores = []

            for model_name, model_metrics in metrics.items():
                r2 = model_metrics.get('r2', 0)
                rmse = model_metrics.get('rmse', float('inf'))

                # Нормализованная оценка (комбинация R² и RMSE)
                # Чем выше R² и ниже RMSE, тем лучше
                normalized_score = r2 - (rmse / np.mean([m.get('rmse', 1) for m in metrics.values()]))

                model_scores.append({
                    'model': model_name,
                    'r2': r2,
                    'rmse': rmse,
                    'score': normalized_score
                })

                # Обновляем лучшие модели
                if r2 > comparison['best_r2']['value']:
                    comparison['best_r2'] = {'model': model_name, 'value': r2}

                if rmse < comparison['best_rmse']['value']:
                    comparison['best_rmse'] = {'model': model_name, 'value': rmse}

            # Ранжирование моделей
            comparison['ranking'] = sorted(model_scores, key=lambda x: x['score'], reverse=True)

            return comparison

        except Exception as e:
            logger.error(f"Error in model comparison: {e}")
            return {}

    def get_polynomial_coefficients(self, time_indices: np.ndarray, values: np.ndarray, degree: int) -> Dict[str, Any]:
        """Получение коэффициентов полинома"""
        try:
            poly_features = PolynomialFeatures(degree=degree)
            X_poly = poly_features.fit_transform(time_indices.reshape(-1, 1))

            model = LinearRegression()
            model.fit(X_poly, values)

            # Формируем уравнение полинома
            coefficients = []
            coefficients.append(model.intercept_)  # Свободный член
            coefficients.extend(model.coef_[1:])   # Коэффициенты при степенях

            equation_parts = []
            for i, coef in enumerate(coefficients):
                if abs(coef) > 1e-10:
                    if i == 0:
                        equation_parts.append(f"{coef:.3f}")
                    elif i == 1:
                        equation_parts.append(f"{coef:+.3f}x")
                    else:
                        equation_parts.append(f"{coef:+.3f}x^{i}")

            equation = " ".join(equation_parts)

            return {
                'coefficients': coefficients,
                'equation': equation,
                'degree': degree
            }

        except Exception as e:
            logger.error(f"Error getting polynomial coefficients: {e}")
            return {}

    def detect_seasonality(self, values: np.ndarray, max_period: int = 30) -> Dict[str, Any]:
        """Обнаружение сезонности в данных"""
        try:
            from scipy.fft import fft, fftfreq

            # Простое обнаружение сезонности через автокорреляцию
            n = len(values)
            if n < 10:
                return {'has_seasonality': False, 'period': None}

            # Нормализуем данные
            normalized_values = (values - np.mean(values)) / np.std(values)

            # Автокорреляция
            autocorr = np.correlate(normalized_values, normalized_values, mode='full')
            autocorr = autocorr[n-1:]

            # Ищем пики в автокорреляции
            max_correlation = 0
            best_period = None

            for period in range(2, min(max_period, n//2)):
                if period < len(autocorr):
                    correlation = autocorr[period]
                    if correlation > max_correlation and correlation > 0.3:
                        max_correlation = correlation
                        best_period = period

            has_seasonality = max_correlation > 0.5

            return {
                'has_seasonality': has_seasonality,
                'period': best_period,
                'strength': float(max_correlation) if max_correlation > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}")
            return {'has_seasonality': False, 'period': None}