from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from .base_repository import BaseRepository
from ..models.lab2_cache import Lab2DataCache
import logging

logger = logging.getLogger(__name__)


class Lab2CacheRepository(BaseRepository[Lab2DataCache]):
    """Репозиторий для работы с кэшем данных Lab2"""

    def __init__(self):
        super().__init__(Lab2DataCache)

    def find_cached_data(
        self,
        symbol: str,
        data_type: str,
        interval: str,
        days: int
    ) -> List[Lab2DataCache]:
        """Поиск кэшированных данных"""
        db = self._get_db()
        try:
            # Вычисляем временные рамки
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            return (
                db.query(self.model_class)
                .filter(
                    and_(
                        self.model_class.symbol == symbol.upper(),
                        self.model_class.data_type == data_type,
                        self.model_class.interval == interval,
                        self.model_class.timestamp >= start_time,
                        self.model_class.timestamp <= end_time
                    )
                )
                .order_by(self.model_class.timestamp.asc())
                .all()
            )
        finally:
            db.close()

    def is_data_fresh(
        self,
        symbol: str,
        data_type: str,
        interval: str,
        days: int,
        max_age_hours: int = 4
    ) -> bool:
        """Проверка свежести кэшированных данных"""
        db = self._get_db()
        try:
            # Проверяем, когда последний раз обновлялись данные
            latest_record = (
                db.query(self.model_class)
                .filter(
                    and_(
                        self.model_class.symbol == symbol.upper(),
                        self.model_class.data_type == data_type,
                        self.model_class.interval == interval
                    )
                )
                .order_by(desc(self.model_class.created_at))
                .first()
            )

            if not latest_record:
                return False

            # Проверяем возраст данных
            age = datetime.now() - latest_record.created_at
            is_fresh = age.total_seconds() < (max_age_hours * 3600)

            # Проверяем количество записей
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            count = (
                db.query(self.model_class)
                .filter(
                    and_(
                        self.model_class.symbol == symbol.upper(),
                        self.model_class.data_type == data_type,
                        self.model_class.interval == interval,
                        self.model_class.timestamp >= start_time
                    )
                )
                .count()
            )

            # Ожидаемое количество записей
            if interval == "60":  # 1 час
                expected_count = days * 24 * 0.8  # 80% от ожидаемого (учитывая выходные)
            elif interval == "240":  # 4 часа
                expected_count = days * 6 * 0.8
            else:  # 1 день
                expected_count = days * 0.8

            has_enough_data = count >= expected_count

            logger.info(f"Data freshness check for {symbol}: is_fresh={is_fresh}, has_enough_data={has_enough_data}, count={count}, expected={expected_count}")

            return is_fresh and has_enough_data

        finally:
            db.close()

    def save_cached_data(self, data_list: List[dict], symbol: str, data_type: str, interval: str) -> int:
        """Сохранение данных в кэш"""
        if not data_list:
            return 0

        db = self._get_db()
        try:
            # Удаляем старые данные для этого символа и интервала
            db.query(self.model_class).filter(
                and_(
                    self.model_class.symbol == symbol.upper(),
                    self.model_class.data_type == data_type,
                    self.model_class.interval == interval
                )
            ).delete()

            # Добавляем новые данные
            cache_records = []
            for item in data_list:
                cache_record = Lab2DataCache(
                    symbol=symbol.upper(),
                    data_type=data_type,
                    interval=interval,
                    timestamp=item['timestamp'],
                    open_price=item.get('open_price'),
                    high_price=item.get('high_price'),
                    low_price=item.get('low_price'),
                    close_price=item.get('close_price'),
                    volume=item.get('volume'),
                    turnover=item.get('turnover')
                )
                cache_records.append(cache_record)

            db.add_all(cache_records)
            db.commit()

            logger.info(f"Saved {len(cache_records)} records for {symbol} ({interval})")
            return len(cache_records)

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving cached data: {e}")
            return 0
        finally:
            db.close()

    def cleanup_old_data(self, days_to_keep: int = 90):
        """Очистка старых данных"""
        db = self._get_db()
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            deleted_count = (
                db.query(self.model_class)
                .filter(self.model_class.created_at < cutoff_date)
                .delete()
            )

            db.commit()
            logger.info(f"Cleaned up {deleted_count} old cache records")
            return deleted_count

        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up old data: {e}")
            return 0
        finally:
            db.close()

    def get_cache_stats(self) -> dict:
        """Получение статистики кэша"""
        db = self._get_db()
        try:
            from sqlalchemy import func, distinct

            stats = (
                db.query(
                    func.count().label('total_records'),
                    func.count(distinct(self.model_class.symbol)).label('unique_symbols'),
                    func.min(self.model_class.timestamp).label('oldest_data'),
                    func.max(self.model_class.timestamp).label('newest_data')
                )
                .first()
            )

            return {
                'total_records': stats.total_records or 0,
                'unique_symbols': stats.unique_symbols or 0,
                'oldest_data': stats.oldest_data,
                'newest_data': stats.newest_data
            }

        finally:
            db.close()