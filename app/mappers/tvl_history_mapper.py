from typing import Dict, Any
from datetime import datetime
from ..models import TVLHistory
from ..schemas.defi_schemas import TVLHistoryResponse


class TVLHistoryMapper:
    """Mapper для преобразования данных истории TVL"""
    
    @staticmethod
    def to_response(tvl_history: TVLHistory) -> TVLHistoryResponse:
        """Преобразование модели в DTO для ответа"""
        return TVLHistoryResponse(
            id=tvl_history.id,
            protocol_id=tvl_history.protocol_id,
            timestamp=tvl_history.timestamp,
            tvl=tvl_history.tvl,
            tvl_change_24h=tvl_history.tvl_change_24h,
            tvl_change_percentage_24h=tvl_history.tvl_change_percentage_24h
        )
    
    @staticmethod
    def from_api_data(protocol_id: str, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных из API в формат для базы данных"""
        return {
            'protocol_id': protocol_id,
            'timestamp': datetime.utcnow(),
            'tvl': float(api_data.get('tvl', 0)) if api_data.get('tvl') is not None else 0.0,
            'tvl_change_24h': api_data.get('change_1d'),
            'tvl_change_percentage_24h': api_data.get('change_1d')
        }
    
    @staticmethod
    def from_historical_data(protocol_id: str, timestamp: datetime, tvl: float) -> Dict[str, Any]:
        """Преобразование исторических данных"""
        return {
            'protocol_id': protocol_id,
            'timestamp': timestamp,
            'tvl': tvl,
            'tvl_change_24h': None,
            'tvl_change_percentage_24h': None
        }