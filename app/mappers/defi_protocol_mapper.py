from typing import List, Optional, Dict, Any
from datetime import datetime
from ..models.crypto import DeFiProtocol, TVLHistory
from ..schemas.defi_schemas import (
    DeFiProtocolResponse,
    DeFiProtocolDetailResponse,
    DeFiProtocolListItem,
    TVLSummary
)


class DeFiProtocolMapper:
    """Mapper для преобразования данных DeFi протоколов"""
    
    @staticmethod
    def to_response(protocol: DeFiProtocol) -> DeFiProtocolResponse:
        """Преобразование модели в DTO для ответа"""
        return DeFiProtocolResponse(
            id=protocol.id,
            name=protocol.name,
            category=protocol.category,
            chain=protocol.chain,
            tvl=protocol.tvl,
            native_token_id=protocol.native_token_id,
            website=protocol.website,
            description=protocol.description,
            created_at=protocol.created_at,
            updated_at=protocol.updated_at
        )
    
    @staticmethod
    def to_detail_response(
        protocol: DeFiProtocol,
        tvl_history: List[TVLHistory] = None
    ) -> DeFiProtocolDetailResponse:
        """Преобразование в детальный DTO с историей TVL"""
        # Импорт внутри метода для избежания циклических зависимостей
        from .tvl_history_mapper import TVLHistoryMapper
        
        return DeFiProtocolDetailResponse(
            id=protocol.id,
            name=protocol.name,
            category=protocol.category,
            chain=protocol.chain,
            tvl=protocol.tvl,
            native_token_id=protocol.native_token_id,
            website=protocol.website,
            description=protocol.description,
            created_at=protocol.created_at,
            updated_at=protocol.updated_at,
            tvl_history=[
                TVLHistoryMapper.to_response(tvl) for tvl in (tvl_history or [])
            ]
        )
    
    @staticmethod
    def to_list_item(protocol_data: Dict[str, Any]) -> DeFiProtocolListItem:
        """Преобразование словаря данных в элемент списка"""
        return DeFiProtocolListItem(
            id=protocol_data.get('id', ''),
            name=protocol_data.get('name', ''),
            category=protocol_data.get('category'),
            chain=protocol_data.get('chain'),
            tvl=protocol_data.get('tvl'),
            tvl_change_24h=protocol_data.get('tvl_change_24h'),
            tvl_change_percentage_24h=protocol_data.get('tvl_change_percentage_24h'),
            updated_at=protocol_data.get('updated_at', datetime.utcnow())
        )
    
    @staticmethod
    def from_api_data(api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразование данных из API в формат для базы данных"""
        # Обработка данных от DefiLlama API
        protocol_id = api_data.get('id') or api_data.get('slug') or api_data.get('name', '').lower().replace(' ', '-')
        
        return {
            'id': protocol_id,
            'name': api_data.get('name', ''),
            'category': api_data.get('category') or api_data.get('classification'),
            'chain': api_data.get('chain') or api_data.get('chains', ['Unknown'])[0] if api_data.get('chains') else 'Unknown',
            'tvl': float(api_data.get('tvl', 0)) if api_data.get('tvl') is not None else None,
            'native_token_id': api_data.get('token'),
            'website': api_data.get('url') or api_data.get('website'),
            'description': api_data.get('description'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    
    @staticmethod
    def calculate_tvl_summary(protocols: List[Dict[str, Any]]) -> TVLSummary:
        """Вычисление суммарной статистики TVL"""
        if not protocols:
            return TVLSummary(
                total_tvl=0.0,
                protocols_count=0,
                top_protocol=None,
                top_protocol_tvl=None
            )
        
        total_tvl = sum(p.get('tvl', 0) or 0 for p in protocols)
        protocols_count = len(protocols)
        
        # Поиск протокола с максимальным TVL
        top_protocol_data = max(protocols, key=lambda x: x.get('tvl', 0) or 0)
        top_protocol = top_protocol_data.get('name')
        top_protocol_tvl = top_protocol_data.get('tvl')
        
        return TVLSummary(
            total_tvl=total_tvl,
            protocols_count=protocols_count,
            top_protocol=top_protocol,
            top_protocol_tvl=top_protocol_tvl
        )