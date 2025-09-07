#!/usr/bin/env python3
"""
Main entry point for running the Crypto DeFi Analyzer application.
This script provides different modes of operation for development and production.
"""

import os
import sys
import asyncio
import argparse
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.services.batch_processor import data_processor
from app.core.database import create_database
from alembic.config import Config
from alembic import command


def init_database():
    """Initialize the database and create tables."""
    print("🔄 Initializing database...")
    try:
        create_database()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)


def run_alembic_migrations():
    """Run Alembic database migrations using standard 'alembic upgrade head'."""
    print("🔄 Running Alembic migrations (alembic upgrade head)...")
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
    except Exception as e:
        print(f"❌ Failed to run migrations: {e}")
        sys.exit(1)


def create_migration_with_autogenerate(message: str):
    """Create new Alembic migration with autogenerate (standard approach)."""
    print(f"🔄 Creating migration with autogenerate: {message}")
    print("   Using: alembic revision --autogenerate -m '{message}'")
    try:
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, message=message, autogenerate=True)
        print("✅ Migration created successfully!")
    except Exception as e:
        print(f"❌ Failed to create migration: {e}")
        sys.exit(1)


def create_empty_migration(message: str):
    """Create empty Alembic migration (without autogenerate)."""
    print(f"🔄 Creating empty migration: {message}")
    print("   Using: alembic revision -m '{message}'")
    try:
        alembic_cfg = Config("alembic.ini")
        command.revision(alembic_cfg, message=message, autogenerate=False)
        print("✅ Empty migration created successfully!")
    except Exception as e:
        print(f"❌ Failed to create migration: {e}")
        sys.exit(1)


def show_migration_history():
    """Show migration history."""
    print("📜 Migration history:")
    try:
        alembic_cfg = Config("alembic.ini")
        command.history(alembic_cfg, verbose=True)
    except Exception as e:
        print(f"❌ Failed to show migration history: {e}")


def show_current_migration():
    """Show current migration."""
    print("📍 Current migration:")
    try:
        alembic_cfg = Config("alembic.ini")
        command.current(alembic_cfg, verbose=True)
    except Exception as e:
        print(f"❌ Failed to show current migration: {e}")


async def load_initial_data():
    """Load initial data from APIs."""
    print("🔄 Loading initial data...")
    try:
        await data_processor.run_full_data_processing()
        print("✅ Initial data loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to load initial data: {e}")
        sys.exit(1)


def run_development_server():
    """Run the development server with auto-reload."""
    print("🚀 Starting development server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📊 API documentation: http://localhost:8000/docs")
    print("🔧 Interactive API: http://localhost:8000/redoc")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )


def run_production_server():
    """Run the production server."""
    print("🚀 Starting production server...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        log_level="warning",
        access_log=False
    )


async def run_scheduler():
    """Run the data scheduler."""
    print("⏰ Starting data scheduler...")
    from app.scheduler import main as scheduler_main
    await scheduler_main()


def main():
    """Main entry point with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Crypto DeFi Analyzer - Cryptocurrency and DeFi data analysis platform"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Database commands
    subparsers.add_parser('init-db', help='Initialize database and create tables')
    
    # Alembic commands (стандартные)
    migrate_parser = subparsers.add_parser('migrate', help='Run migrations (alembic upgrade head)')
    
    migration_parser = subparsers.add_parser('make-migration', help='Create migration with autogenerate')
    migration_parser.add_argument('message', help='Migration message')
    
    empty_migration_parser = subparsers.add_parser('make-empty-migration', help='Create empty migration')
    empty_migration_parser.add_argument('message', help='Migration message')
    
    subparsers.add_parser('migration-history', help='Show migration history')
    subparsers.add_parser('migration-current', help='Show current migration')
    
    # Data commands
    subparsers.add_parser('load-data', help='Load initial data from APIs')
    
    # Server commands
    dev_parser = subparsers.add_parser('dev', help='Run development server')
    dev_parser.add_argument('--port', type=int, default=8000, help='Port to run on')
    
    prod_parser = subparsers.add_parser('prod', help='Run production server')
    prod_parser.add_argument('--workers', type=int, default=4, help='Number of workers')
    
    # Scheduler command
    subparsers.add_parser('scheduler', help='Run data scheduler')
    
    # Setup command (init + migrations + load data)
    subparsers.add_parser('setup', help='Full setup: init database, run migrations and load data')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🏗️  Crypto DeFi Analyzer")
    print("=" * 50)
    
    if args.command == 'init-db':
        init_database()
    
    elif args.command == 'migrate':
        run_alembic_migrations()
    
    elif args.command == 'make-migration':
        create_migration_with_autogenerate(args.message)
    
    elif args.command == 'make-empty-migration':
        create_empty_migration(args.message)
    
    elif args.command == 'migration-history':
        show_migration_history()
        
    elif args.command == 'migration-current':
        show_current_migration()
        
    elif args.command == 'load-data':
        asyncio.run(load_initial_data())
        
    elif args.command == 'dev':
        print(f"Development mode on port {args.port}")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=args.port,
            reload=True,
            log_level="info"
        )
        
    elif args.command == 'prod':
        print(f"Production mode with {args.workers} workers")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            workers=args.workers,
            log_level="warning"
        )
        
    elif args.command == 'scheduler':
        asyncio.run(run_scheduler())
        
    elif args.command == 'setup':
        init_database()
        run_alembic_migrations()
        asyncio.run(load_initial_data())
        print("🎉 Full setup completed! You can now run 'python run.py dev' to start the server.")


if __name__ == "__main__":
    main()