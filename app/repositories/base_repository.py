from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generic, TypeVar
from datetime import datetime, timedelta
from ..core.database import clickhouse_manager

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Базовый репозиторий с общими методами для работы с ClickHouse"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.db = clickhouse_manager
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """Выполнение SQL запроса"""
        return self.db.execute_query(query, parameters or {})
    
    def insert_data(self, data: List[Dict[str, Any]]) -> None:
        """Вставка данных в таблицу"""
        if data:
            self.db.insert_data(self.table_name, data)
    
    def insert_single(self, data: Dict[str, Any]) -> None:
        """Вставка одной записи"""
        self.insert_data([data])
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Получение всех записей с пагинацией"""
        query = f"""
        SELECT * FROM {self.table_name}
        ORDER BY created_at DESC
        LIMIT %(limit)s OFFSET %(offset)s
        """
        result = self.execute_query(query, {'limit': limit, 'offset': offset})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def find_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Поиск записи по ID"""
        query = f"""
        SELECT * FROM {self.table_name}
        WHERE id = %(id)s
        LIMIT 1
        """
        result = self.execute_query(query, {'id': entity_id})
        
        if result.result_rows:
            return dict(zip(result.column_names, result.result_rows[0]))
        return None
    
    def count_all(self) -> int:
        """Подсчет общего количества записей"""
        query = f"SELECT count(*) as total FROM {self.table_name}"
        result = self.execute_query(query)
        return result.result_rows[0][0] if result.result_rows else 0
    
    def delete_by_id(self, entity_id: str) -> bool:
        """Удаление записи по ID (если поддерживается ClickHouse)"""
        query = f"""
        ALTER TABLE {self.table_name} DELETE WHERE id = %(id)s
        """
        try:
            self.execute_query(query, {'id': entity_id})
            return True
        except Exception:
            return False
    
    def find_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Поиск записей в диапазоне дат (требует поле timestamp)"""
        query = f"""
        SELECT * FROM {self.table_name}
        WHERE timestamp >= %(start_date)s AND timestamp <= %(end_date)s
        ORDER BY timestamp DESC
        LIMIT %(limit)s
        """
        result = self.execute_query(query, {
            'start_date': start_date,
            'end_date': end_date,
            'limit': limit
        })
        return [dict(zip(result.column_names, row)) for row in result.result_rows]
    
    def find_recent(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Поиск записей за последние N часов"""
        start_date = datetime.utcnow() - timedelta(hours=hours)
        end_date = datetime.utcnow()
        return self.find_by_date_range(start_date, end_date, limit)