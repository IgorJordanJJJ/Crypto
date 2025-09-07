#!/usr/bin/env bash
set -e

echo "🚀 Initializing Superset for Crypto DeFi Analyzer..."

# Ждем пока PostgreSQL и Redis будут готовы  
echo "⏳ Waiting for services to be ready..."
sleep 15

# Устанавливаем драйверы перед инициализацией
echo "🔌 Installing database drivers..."
pip install psycopg2-binary

# Инициализируем базу данных Superset (PostgreSQL)
echo "📊 Initializing Superset metadata database..."
superset db upgrade

# Создаем администратора если он еще не создан
echo "👤 Creating admin user..."
superset fab create-admin --username admin --firstname Admin --lastname User --email admin@crypto-analytics.local --password admin

# Инициализируем Superset
echo "⚙️ Initializing Superset..."
superset init

echo "✅ Superset initialization completed!"
echo "📊 PostgreSQL: Metadata storage (users, dashboards, settings)"
echo "🏪 PostgreSQL: Data source for analytics"
echo "🌐 Access Superset at http://localhost:8088"  
echo "🔑 Login: admin / Password: admin"

# Запускаем Superset
/usr/bin/run-server.sh