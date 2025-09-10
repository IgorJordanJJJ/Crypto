from typing import Dict, Any
from datetime import datetime
from ..models import PriceHistory
from ..schemas.crypto_schemas import PriceHistoryResponse


class PriceHistoryMapper:
    """Маппер для преобразования данных истории цен"""
    
    @staticmethod
    def to_response(price_history: PriceHistory) -> PriceHistoryResponse:
        """Преобразование модели в DTO для ответа"""
        return PriceHistoryResponse(
            id=price_history.id,
            cryptocurrency_id=price_history.cryptocurrency_id,
            timestamp=price_history.timestamp,
            price_usd=price_history.price_usd,
            volume_24h=price_history.volume_24h,
            market_cap=price_history.market_cap,
            price_change_24h=price_history.price_change_24h,
            price_change_percentage_24h=price_history.price_change_percentage_24h
        )
    
    @staticmethod
    def from_api_data(crypto_id: str, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных из API в формат для базы данных"""
        return {
            'cryptocurrency_id': crypto_id,
            'timestamp': datetime.utcnow(),
            'price_usd': api_data.get('current_price', 0),
            'volume_24h': api_data.get('total_volume'),
            'market_cap': api_data.get('market_cap'),
            'price_change_24h': api_data.get('price_change_24h'),
            'price_change_percentage_24h': api_data.get('price_change_percentage_24h')
        }