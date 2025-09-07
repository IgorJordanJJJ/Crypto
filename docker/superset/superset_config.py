# -*- coding: utf-8 -*-
"""
Superset configuration for Crypto DeFi Analyzer
"""
import os
from datetime import timedelta

# Superset metadata database connection - PostgreSQL для метаданных
SQLALCHEMY_DATABASE_URI = f"postgresql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_PASSWORD']}@{os.environ['DATABASE_HOST']}:{os.environ['DATABASE_PORT']}/{os.environ['DATABASE_DB']}"

# Redis configuration for caching and Celery  
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', 6379)

# Cache configuration - Redis кэш для производительности
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24,  # 1 day
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': 1,
}

# Celery configuration for async queries
class CeleryConfig:
    CELERY_IMPORTS = ('superset.sql_lab',)
    CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '10/s'}}
    BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
    CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

CELERY_CONFIG = CeleryConfig

# Feature flags
FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "EMBEDDED_SUPERSET": True,
    "ESCAPE_MARKDOWN_HTML": True,
    "DASHBOARD_CROSS_FILTERS": True,
}

# Security settings
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'your_secret_key_here')

# CORS settings for integration with main app
ENABLE_CORS = True
CORS_OPTIONS = {
    'supports_credentials': True,
    'allow_headers': ['*'],
    'resources': ['*'],
    'origins': ['http://localhost:8000', 'http://localhost:3000']
}

# Query timeout
SUPERSET_WEBSERVER_TIMEOUT = 60

# SQL Lab settings
SQL_MAX_ROW = 100000
SUPERSET_WORKERS = 2
SUPERSET_WORKER_TIMEOUT = 300

# Email configuration (optional)
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PORT = os.environ.get('SMTP_PORT', 587)
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
SMTP_MAIL_FROM = os.environ.get('SMTP_MAIL_FROM')

# Logging configuration
ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = "DEBUG"
FILENAME = os.path.join("/app/superset_home", "superset.log")

# Custom CSS (optional)
CSS_TEMPLATES = [
    'dashboard_crypto.css'
]

# Dashboard auto-refresh intervals
DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [10, "10 seconds"],
    [30, "30 seconds"],
    [60, "1 minute"],
    [300, "5 minutes"],
    [1800, "30 minutes"],
    [3600, "1 hour"],
]

# Chart configuration
DEFAULT_FEATURE_FLAGS = {
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": False,
    "PRESTO_EXPAND_DATA": True,
}

# Row limit in query results
ROW_LIMIT = 50000

# Timezone
DEFAULT_TIMEZONE = "UTC"