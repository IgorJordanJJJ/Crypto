.PHONY: help install dev prod setup clean test docker-build docker-up docker-down

# Default target
help:
	@echo "🏗️  Crypto DeFi Analyzer - Available Commands"
	@echo "=================================================="
	@echo "📦 install      - Install dependencies with Poetry"
	@echo "🔧 setup        - Initialize database and load initial data"
	@echo "🚀 dev          - Run development server"
	@echo "🏭 prod         - Run production server"
	@echo "⏰ scheduler    - Run data scheduler"
	@echo "🧪 test         - Run tests (when implemented)"
	@echo "🧹 clean        - Clean temporary files"
	@echo "🐳 docker-build - Build Docker image"
	@echo "🐳 docker-up    - Start with Docker Compose"
	@echo "🐳 docker-down  - Stop Docker Compose"
	@echo ""
	@echo "📖 For more information, see README.md"

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	poetry install

# Initialize and setup
setup:
	@echo "🔧 Setting up the application..."
	python run.py setup

# Development server
dev:
	@echo "🚀 Starting development server..."
	python run.py dev

# Production server
prod:
	@echo "🏭 Starting production server..."
	python run.py prod

# Data scheduler
scheduler:
	@echo "⏰ Starting data scheduler..."
	python run.py scheduler

# Initialize database only
init-db:
	@echo "🗄️  Initializing database..."
	python run.py init-db

# Load data only
load-data:
	@echo "📊 Loading initial data..."
	python run.py load-data

# Run tests (placeholder for future implementation)
test:
	@echo "🧪 Running tests..."
	@echo "Tests will be implemented in future versions"

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t crypto-defi-analyzer .

docker-up:
	@echo "🐳 Starting services with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker Compose services..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Development helpers
format:
	@echo "🎨 Formatting code..."
	poetry run black app/
	poetry run isort app/

lint:
	@echo "🔍 Linting code..."
	poetry run flake8 app/

# Check system requirements
check:
	@echo "✅ Checking system requirements..."
	@python --version
	@echo "Poetry version:"
	@poetry --version
	@echo "Docker version:"
	@docker --version 2>/dev/null || echo "Docker not installed"
	@echo "Docker Compose version:"
	@docker-compose --version 2>/dev/null || echo "Docker Compose not installed"

# Show project status
status:
	@echo "📊 Project Status"
	@echo "=================="
	@echo "Python version: $(shell python --version)"
	@echo "Poetry version: $(shell poetry --version)"
	@echo "Project directory: $(PWD)"
	@echo "Environment file: $(shell test -f .env && echo "✅ Found" || echo "❌ Missing (.env.example available)")"
	@echo ""
	@echo "📁 Project structure:"
	@tree -I '__pycache__|*.pyc|.git' -L 2