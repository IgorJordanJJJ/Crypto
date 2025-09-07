from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.crypto import Cryptocurrency, PriceHistory, MarketData
from ..schemas.crypto_schemas import (
    CryptocurrencyResponse, 
    CryptocurrencyDetailResponse,
    CryptocurrencyListItem
)


class CryptocurrencyMapper:
    """Маппер для преобразования данных криптовалют"""
    
    @staticmethod
    def to_response(crypto: Cryptocurrency) -> CryptocurrencyResponse:
        """Преобразование модели в DTO для ответа"""
        return CryptocurrencyResponse(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            market_cap_rank=crypto.market_cap_rank,
            description=crypto.description,
            website=crypto.website,
            blockchain=crypto.blockchain,
            created_at=crypto.created_at,
            updated_at=crypto.updated_at
        )
    
    @staticmethod
    def to_detail_response(
        crypto: Cryptocurrency, 
        price_history: List[PriceHistory] = None,
        market_data: List[MarketData] = None
    ) -> CryptocurrencyDetailResponse:
        """Преобразование в детальный DTO с историей"""
        from .price_history_mapper import PriceHistoryMapper
        from .market_data_mapper import MarketDataMapper
        
        return CryptocurrencyDetailResponse(
            id=crypto.id,
            symbol=crypto.symbol,
            name=crypto.name,
            market_cap_rank=crypto.market_cap_rank,
            description=crypto.description,
            website=crypto.website,
            blockchain=crypto.blockchain,
            created_at=crypto.created_at,
            updated_at=crypto.updated_at,
            price_history=[
                PriceHistoryMapper.to_response(ph) for ph in (price_history or [])
            ],
            market_data=[
                MarketDataMapper.to_response(md) for md in (market_data or [])
            ]
        )
    
    @staticmethod
    def to_list_item(crypto_data: Dict[str, Any]) -> CryptocurrencyListItem:
        """Преобразование словаря данных в элемент списка"""
        return CryptocurrencyListItem(
            id=crypto_data.get('id', ''),
            symbol=crypto_data.get('symbol', ''),
            name=crypto_data.get('name', ''),
            market_cap_rank=crypto_data.get('market_cap_rank'),
            current_price=crypto_data.get('current_price'),
            price_change_24h=crypto_data.get('price_change_24h'),
            price_change_percentage_24h=crypto_data.get('price_change_percentage_24h'),
            market_cap=crypto_data.get('market_cap'),
            updated_at=crypto_data.get('updated_at', datetime.utcnow())
        )
    
    @staticmethod
    def from_api_data(api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных из API в формат для базы данных"""
        return {
            'id': api_data.get('id'),
            'symbol': api_data.get('symbol', '').lower(),
            'name': api_data.get('name', ''),
            'market_cap_rank': api_data.get('market_cap_rank'),
            'description': api_data.get('description', {}).get('en') if isinstance(api_data.get('description'), dict) else api_data.get('description'),
            'website': api_data.get('links', {}).get('homepage', [None])[0] if api_data.get('links') else api_data.get('website'),
            'blockchain': api_data.get('asset_platform_id') or api_data.get('blockchain'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }