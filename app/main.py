from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from .controllers.crypto_controller import create_crypto_router, create_analytics_router
from .controllers.defi_controller import create_defi_router
from .controllers.data_controller import create_data_router
from .controllers.web_controller import create_web_router
from .core.config import settings
from .core.database import clickhouse_manager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        logger.info("Initializing database...")
        clickhouse_manager.create_database()
        clickhouse_manager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Cryptocurrency and DeFi data analysis platform with HTMX",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include all routers
app.include_router(create_web_router())  # Web pages and HTMX endpoints
app.include_router(create_crypto_router())  # Cryptocurrency API
app.include_router(create_defi_router())  # DeFi API
app.include_router(create_analytics_router())  # Analytics API
app.include_router(create_data_router())  # Data management API


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        clickhouse_manager.execute_query("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.app_version
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "version": settings.app_version
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )