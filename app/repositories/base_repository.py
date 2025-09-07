from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generic, TypeVar
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from ..core.database import get_db

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Базовый репозиторий с общими методами для работы с PostgreSQL через SQLAlchemy"""
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    def _get_db(self) -> Session:
        """Получение сессии базы данных"""
        db = next(get_db())
        return db
    
    def create(self, obj: T) -> T:
        """Создание новой записи"""
        db = self._get_db()
        try:
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()
    
    def create_many(self, objs: List[T]) -> List[T]:
        """Создание нескольких записей"""
        db = self._get_db()
        try:
            db.add_all(objs)
            db.commit()
            for obj in objs:
                db.refresh(obj)
            return objs
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Получение всех записей с пагинацией"""
        db = self._get_db()
        try:
            return db.query(self.model_class).offset(offset).limit(limit).all()
        finally:
            db.close()
    
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """Поиск записи по ID"""
        db = self._get_db()
        try:
            return db.query(self.model_class).filter(self.model_class.id == entity_id).first()
        finally:
            db.close()
    
    def count_all(self) -> int:
        """Подсчет общего количества записей"""
        db = self._get_db()
        try:
            return db.query(self.model_class).count()
        finally:
            db.close()
    
    def update(self, obj: T) -> T:
        """Обновление записи"""
        db = self._get_db()
        try:
            db.merge(obj)
            db.commit()
            return obj
        except SQLAlchemyError:
            db.rollback()
            raise
        finally:
            db.close()
    
    def delete_by_id(self, entity_id: str) -> bool:
        """Удаление записи по ID"""
        db = self._get_db()
        try:
            obj = db.query(self.model_class).filter(self.model_class.id == entity_id).first()
            if obj:
                db.delete(obj)
                db.commit()
                return True
            return False
        except SQLAlchemyError:
            db.rollback()
            return False
        finally:
            db.close()
    
    def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[T]:
        """Поиск записей в диапазоне дат (требует поле timestamp)"""
        db = self._get_db()
        try:
            return (db.query(self.model_class)
                   .filter(self.model_class.timestamp >= start_date)
                   .filter(self.model_class.timestamp <= end_date)
                   .order_by(self.model_class.timestamp.desc())
                   .limit(limit)
                   .all())
        finally:
            db.close()
    
    def find_recent(self, hours: int = 24, limit: int = 100) -> List[T]:
        """Поиск записей за последние N часов"""
        start_date = datetime.utcnow() - timedelta(hours=hours)
        end_date = datetime.utcnow()
        return self.find_by_date_range(start_date, end_date, limit)