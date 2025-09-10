from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
from .config import settings


DATABASE_URL = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations():
    """Run Alembic migrations programmatically"""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Get the project root directory (where alembic.ini is located)
        from pathlib import Path
        project_root = Path(__file__).parent.parent.parent
        alembic_cfg_path = project_root / "alembic.ini"
        
        if not alembic_cfg_path.exists():
            raise FileNotFoundError(f"alembic.ini not found at {alembic_cfg_path}")
        
        alembic_cfg = Config(str(alembic_cfg_path))
        command.upgrade(alembic_cfg, "head")
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False


def get_engine():
    """Get the SQLAlchemy engine"""
    return engine