from typing import Dict, Any
from datetime import datetime
from ..models import MarketData
from ..schemas.crypto_schemas import MarketDataResponse


class MarketDataMapper:
    """Маппер для преобразования рыночных данных"""
    
    @staticmethod
    def to_response(market_data: MarketData) -> MarketDataResponse:
        """Преобразование модели в DTO для ответа"""
        return MarketDataResponse(
            id=market_data.id,
            cryptocurrency_id=market_data.cryptocurrency_id,
            timestamp=market_data.timestamp,
            total_supply=market_data.total_supply,
            circulating_supply=market_data.circulating_supply,
            max_supply=market_data.max_supply,
            ath=market_data.ath,
            atl=market_data.atl,
            ath_date=market_data.ath_date,
            atl_date=market_data.atl_date,
            roi_percentage=market_data.roi_percentage
        )
    
    @staticmethod
    def from_api_data(crypto_id: str, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных из API в формат для базы данных"""
        return {
            'cryptocurrency_id': crypto_id,
            'timestamp': datetime.utcnow(),
            'total_supply': api_data.get('total_supply'),
            'circulating_supply': api_data.get('circulating_supply'),
            'max_supply': api_data.get('max_supply'),
            'ath': api_data.get('ath'),
            'atl': api_data.get('atl'),
            'ath_date': datetime.fromisoformat(api_data['ath_date'].replace('Z', '+00:00')) if api_data.get('ath_date') else None,
            'atl_date': datetime.fromisoformat(api_data['atl_date'].replace('Z', '+00:00')) if api_data.get('atl_date') else None,
            'roi_percentage': api_data.get('roi', {}).get('percentage') if api_data.get('roi') else None
        }