from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from .controllers.crypto_controller import create_crypto_router, create_analytics_router
from .controllers.defi_controller import create_defi_router
from .controllers.data_controller import create_data_router
from .controllers.web_controller import create_web_router
from .controllers.lab2_controller import create_lab2_router
from .controllers.lab3_controller import create_lab3_router
from .controllers.lab4_controller import create_lab4_router
from .core.config import settings
from .core.database import get_engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup - database should be migrated via Alembic")
    
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
app.include_router(create_lab2_router())  # Lab 2 Statistical Analysis
app.include_router(create_lab3_router())  # Lab 3 Polynomial Approximation
app.include_router(create_lab4_router())  # Lab 4 Data Clustering


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute("SELECT 1")
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
    import sys
    from pathlib import Path
    
    # Add the project root to Python path when running directly
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )