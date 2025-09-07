from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from ..repositories.crypto_repository import CryptocurrencyRepository
from ..repositories.price_history_repository import PriceHistoryRepository
from ..repositories.defi_repository import DeFiProtocolRepository
from ..repositories.tvl_history_repository import TVLHistoryRepository
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")


class WebController:
    """Контроллер для веб-страниц с HTMX"""
    
    def __init__(self):
        self.crypto_repo = CryptocurrencyRepository()
        self.price_repo = PriceHistoryRepository()
        self.defi_repo = DeFiProtocolRepository()
        self.tvl_repo = TVLHistoryRepository()
    
    async def index_page(self, request: Request) -> HTMLResponse:
        """Главная страница"""
        try:
            # Получаем базовую статистику для главной страницы
            crypto_count = self.crypto_repo.count_all()
            defi_count = self.defi_repo.count_all()
            
            context = {
                "request": request,
                "crypto_count": crypto_count,
                "defi_count": defi_count,
                "page_title": "Crypto DeFi Analyzer"
            }
            
            return templates.TemplateResponse("index.html", context)
            
        except Exception as e:
            logger.error(f"Error in index page: {e}")
            context = {
                "request": request,
                "error": "Ошибка загрузки данных",
                "page_title": "Crypto DeFi Analyzer"
            }
            return templates.TemplateResponse("index.html", context)
    
    async def cryptocurrencies_page(self, request: Request) -> HTMLResponse:
        """Страница криптовалют"""
        return templates.TemplateResponse("cryptocurrencies.html", {
            "request": request,
            "page_title": "Криптовалюты"
        })
    
    async def defi_page(self, request: Request) -> HTMLResponse:
        """Страница DeFi протоколов"""
        return templates.TemplateResponse("defi.html", {
            "request": request,
            "page_title": "DeFi Протоколы"
        })
    
    async def analytics_page(self, request: Request) -> HTMLResponse:
        """Страница аналитики"""
        return templates.TemplateResponse("analytics.html", {
            "request": request,
            "page_title": "Аналитика"
        })
    
    # HTMX-специфичные методы для частичных обновлений
    
    async def crypto_table_partial(
        self,
        request: Request,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> HTMLResponse:
        """Частичное обновление таблицы криптовалют через HTMX"""
        try:
            crypto_data = self.crypto_repo.get_cryptocurrencies_with_latest_price(
                limit=limit,
                offset=offset
            )
            
            if search:
                search_lower = search.lower()
                crypto_data = [
                    crypto for crypto in crypto_data
                    if (crypto.get('name', '').lower().find(search_lower) >= 0 or
                        crypto.get('symbol', '').lower().find(search_lower) >= 0)
                ]
            
            return templates.TemplateResponse("partials/crypto_table.html", {
                "request": request,
                "cryptocurrencies": crypto_data,
                "current_page": offset // limit + 1
            })
            
        except Exception as e:
            logger.error(f"Error in crypto table partial: {e}")
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error_message": "Ошибка загрузки данных криптовалют"
            })
    
    async def defi_table_partial(
        self,
        request: Request,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        chain: Optional[str] = None
    ) -> HTMLResponse:
        """Частичное обновление таблицы DeFi протоколов через HTMX"""
        try:
            protocol_data = self.defi_repo.get_protocols_with_latest_tvl(
                limit=limit,
                offset=offset
            )
            
            # Применяем фильтры
            if category:
                protocol_data = [p for p in protocol_data if p.get('category') == category]
            
            if chain:
                protocol_data = [p for p in protocol_data if p.get('chain') == chain]
            
            return templates.TemplateResponse("partials/defi_table.html", {
                "request": request,
                "protocols": protocol_data,
                "current_page": offset // limit + 1
            })
            
        except Exception as e:
            logger.error(f"Error in defi table partial: {e}")
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error_message": "Ошибка загрузки данных DeFi протоколов"
            })
    
    async def crypto_details_modal(self, request: Request, crypto_id: str) -> HTMLResponse:
        """Модальное окно с деталями криптовалюты"""
        try:
            crypto_data = self.crypto_repo.find_by_id(crypto_id)
            if not crypto_data:
                return templates.TemplateResponse("partials/error.html", {
                    "request": request,
                    "error_message": "Криптовалюта не найдена"
                })
            
            # Получаем историю цен
            price_history = self.price_repo.find_by_crypto_id(crypto_id, days=30)
            
            return templates.TemplateResponse("partials/crypto_details_modal.html", {
                "request": request,
                "cryptocurrency": crypto_data,
                "price_history": price_history[:10]  # Ограничиваем для отображения в таблице
            })
            
        except Exception as e:
            logger.error(f"Error in crypto details modal: {e}")
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error_message": "Ошибка загрузки деталей криптовалюты"
            })
    
    async def defi_details_modal(self, request: Request, protocol_id: str) -> HTMLResponse:
        """Модальное окно с деталями DeFi протокола"""
        try:
            protocol_data = self.defi_repo.find_by_id(protocol_id)
            if not protocol_data:
                return templates.TemplateResponse("partials/error.html", {
                    "request": request,
                    "error_message": "Протокол не найден"
                })
            
            # Получаем историю TVL
            tvl_history = self.tvl_repo.find_by_protocol_id(protocol_id, days=30)
            
            return templates.TemplateResponse("partials/defi_details_modal.html", {
                "request": request,
                "protocol": protocol_data,
                "tvl_history": tvl_history[:10]  # Ограничиваем для отображения в таблице
            })
            
        except Exception as e:
            logger.error(f"Error in defi details modal: {e}")
            return templates.TemplateResponse("partials/error.html", {
                "request": request,
                "error_message": "Ошибка загрузки деталей протокола"
            })


def create_web_router() -> APIRouter:
    """Создание роутера для веб-страниц"""
    router = APIRouter(tags=["web"])
    controller = WebController()
    
    # Основные страницы
    @router.get("/", response_class=HTMLResponse)
    async def index_page(request: Request):
        return await controller.index_page(request)
    
    @router.get("/cryptocurrencies", response_class=HTMLResponse)
    async def cryptocurrencies_page(request: Request):
        return await controller.cryptocurrencies_page(request)
    
    @router.get("/defi", response_class=HTMLResponse)
    async def defi_page(request: Request):
        return await controller.defi_page(request)
    
    @router.get("/analytics", response_class=HTMLResponse)
    async def analytics_page(request: Request):
        return await controller.analytics_page(request)
    
    # HTMX эндпоинты для частичных обновлений
    @router.get("/partials/crypto-table", response_class=HTMLResponse)
    async def crypto_table_partial(
        request: Request,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        search: Optional[str] = Query(None)
    ):
        return await controller.crypto_table_partial(request, limit, offset, search)
    
    @router.get("/partials/defi-table", response_class=HTMLResponse)
    async def defi_table_partial(
        request: Request,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        category: Optional[str] = Query(None),
        chain: Optional[str] = Query(None)
    ):
        return await controller.defi_table_partial(request, limit, offset, category, chain)
    
    @router.get("/partials/crypto-details/{crypto_id}", response_class=HTMLResponse)
    async def crypto_details_modal(request: Request, crypto_id: str):
        return await controller.crypto_details_modal(request, crypto_id)
    
    @router.get("/partials/defi-details/{protocol_id}", response_class=HTMLResponse)
    async def defi_details_modal(request: Request, protocol_id: str):
        return await controller.defi_details_modal(request, protocol_id)
    
    return router