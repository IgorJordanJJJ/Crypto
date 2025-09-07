# 📊 Apache Superset для Crypto DeFi Analyzer

Apache Superset - мощная платформа для создания интерактивных дашбордов и визуализации данных. В рамках проекта **Crypto DeFi Analyzer** используется следующая архитектура:

## 🏗️ Архитектура системы

- **🐘 PostgreSQL** - хранит метаданные Superset (пользователи, дашборды, настройки графиков)
- **🏪 ClickHouse** - основной источник данных (криптовалюты, цены, DeFi протоколы, TVL)
- **📦 Redis** - кэширование запросов и очереди для асинхронной обработки
- **📊 Superset** - веб-интерфейс для создания дашбордов и визуализаций

**Важно**: Все графики и аналитика строятся на данных из ClickHouse, а PostgreSQL нужна только для технических нужд Superset.

## 🚀 Быстрый старт

### 1. Запуск системы

```bash
# Запуск всех сервисов включая Superset
docker-compose up -d

# Проверка статуса сервисов
docker-compose ps

# Просмотр логов Superset
docker-compose logs -f superset
```

### 2. Доступ к Superset

- **URL**: http://localhost:8088
- **Логин**: admin
- **Пароль**: admin

⏰ **Важно**: Первый запуск может занять 2-3 минуты для инициализации базы данных.

### 3. Подключение к ClickHouse

После входа в Superset выполните следующие шаги для подключения к вашей базе данных с криптовалютами:

1. **Перейдите в Settings → Database Connections**
2. **Нажмите "+ DATABASE"**  
3. **Выберите "Other" в качестве типа базы данных**
4. **Введите параметры подключения**:

```
DATABASE NAME: Crypto Analytics ClickHouse
SQLALCHEMY URI: clickhouse+http://default:@clickhouse:8123/crypto_analytics
```

5. **Нажмите "TEST CONNECTION"** для проверки подключения к ClickHouse
6. **Сохраните подключение кнопкой "CONNECT"**

💡 **Важно**: 
- **PostgreSQL** хранит настройки Superset, пользователей и конфигурации дашбордов
- **ClickHouse** является источником всех данных для ваших графиков и аналитики
- **Redis** ускоряет работу за счет кэширования часто используемых запросов

## 📈 Готовые дашборды и графики

### 1. 🪙 **Криптовалютный дашборд**

#### График 1: Топ-10 криптовалют по рыночной капитализации
```sql
SELECT 
    name,
    symbol,
    market_cap,
    current_price,
    price_change_percentage_24h
FROM cryptocurrencies c
LEFT JOIN (
    SELECT 
        cryptocurrency_id,
        price_usd as current_price,
        market_cap,
        price_change_percentage_24h,
        ROW_NUMBER() OVER (PARTITION BY cryptocurrency_id ORDER BY timestamp DESC) as rn
    FROM price_history
) p ON c.id = p.cryptocurrency_id AND p.rn = 1
WHERE market_cap > 0
ORDER BY market_cap DESC
LIMIT 10
```

**Тип визуализации**: Table / Big Number with Trendline  
**Описание**: Показывает текущее состояние топ криптовалют с их ценами и изменениями за 24 часа

---

#### График 2: Динамика цен Bitcoin и Ethereum
```sql
SELECT 
    timestamp,
    cryptocurrency_id,
    price_usd
FROM price_history ph
JOIN cryptocurrencies c ON ph.cryptocurrency_id = c.id
WHERE c.symbol IN ('btc', 'eth')
AND timestamp >= now() - INTERVAL 30 DAY
ORDER BY timestamp DESC
```

**Тип визуализации**: Time Series Line Chart  
**Описание**: Сравнение динамики цен BTC и ETH за последний месяц

---

#### График 3: Объемы торгов по дням
```sql
SELECT 
    toDate(timestamp) as date,
    sum(volume_24h) as total_volume,
    count(DISTINCT cryptocurrency_id) as active_cryptos
FROM price_history
WHERE timestamp >= now() - INTERVAL 30 DAY
AND volume_24h > 0
GROUP BY toDate(timestamp)
ORDER BY date DESC
```

**Тип визуализации**: Mixed Chart (Column + Line)  
**Описание**: Показывает общий объем торгов и количество активных криптовалют по дням

---

#### График 4: Распределение криптовалют по блокчейнам
```sql
SELECT 
    COALESCE(blockchain, 'Unknown') as blockchain,
    count(*) as crypto_count,
    sum(market_cap) as total_market_cap
FROM cryptocurrencies c
LEFT JOIN (
    SELECT 
        cryptocurrency_id,
        market_cap,
        ROW_NUMBER() OVER (PARTITION BY cryptocurrency_id ORDER BY timestamp DESC) as rn
    FROM price_history
    WHERE market_cap > 0
) p ON c.id = p.cryptocurrency_id AND p.rn = 1
GROUP BY blockchain
HAVING crypto_count > 1
ORDER BY total_market_cap DESC
```

**Тип визуализации**: Pie Chart / Sunburst Chart  
**Описание**: Распределение рыночной капитализации по различным блокчейнам

---

### 2. 🏦 **DeFi Протоколы дашборд**

#### График 5: Топ DeFi протоколы по TVL
```sql
SELECT 
    name,
    category,
    chain,
    tvl,
    tvl_change_percentage_24h
FROM defi_protocols dp
LEFT JOIN (
    SELECT 
        protocol_id,
        tvl_change_percentage_24h,
        ROW_NUMBER() OVER (PARTITION BY protocol_id ORDER BY timestamp DESC) as rn
    FROM tvl_history
) th ON dp.id = th.protocol_id AND th.rn = 1
WHERE tvl > 1000000
ORDER BY tvl DESC
LIMIT 20
```

**Тип визуализации**: Horizontal Bar Chart  
**Описание**: Топ-20 DeFi протоколов с их TVL и изменениями за 24 часа

---

#### График 6: TVL по категориям DeFi
```sql
SELECT 
    category,
    sum(tvl) as total_tvl,
    count(*) as protocols_count,
    avg(tvl) as avg_tvl
FROM defi_protocols
WHERE tvl > 0 AND category IS NOT NULL
GROUP BY category
ORDER BY total_tvl DESC
```

**Тип визуализации**: Treemap / Pie Chart  
**Описание**: Распределение общего TVL между различными категориями DeFi (DEX, Lending, Yield Farming, etc.)

---

#### График 7: Динамика TVL во времени
```sql
SELECT 
    toDate(timestamp) as date,
    sum(tvl) as total_tvl,
    count(DISTINCT protocol_id) as active_protocols
FROM tvl_history
WHERE timestamp >= now() - INTERVAL 30 DAY
GROUP BY toDate(timestamp)
ORDER BY date DESC
```

**Тип визуализации**: Area Chart  
**Описание**: Показывает изменение общего TVL в DeFi экосистеме за последний месяц

---

#### График 8: Heatmap изменений TVL по протоколам
```sql
SELECT 
    dp.name,
    dp.category,
    th.tvl_change_percentage_24h,
    th.tvl
FROM defi_protocols dp
JOIN (
    SELECT 
        protocol_id,
        tvl,
        tvl_change_percentage_24h,
        ROW_NUMBER() OVER (PARTITION BY protocol_id ORDER BY timestamp DESC) as rn
    FROM tvl_history
    WHERE tvl_change_percentage_24h IS NOT NULL
) th ON dp.id = th.protocol_id AND th.rn = 1
WHERE th.tvl > 1000000
ORDER BY th.tvl_change_percentage_24h DESC
```

**Тип визуализации**: Heatmap  
**Описание**: Тепловая карта показывающая изменения TVL по протоколам - зеленые растут, красные падают

---

### 3. 📊 **Сводный аналитический дашборд**

#### График 9: Корреляция между ценами криптовалют и TVL DeFi
```sql
SELECT 
    toDate(ph.timestamp) as date,
    sum(ph.price_usd * ph.volume_24h) / sum(ph.volume_24h) as avg_crypto_price,
    (SELECT sum(tvl) FROM tvl_history WHERE toDate(timestamp) = date) as total_tvl
FROM price_history ph
JOIN cryptocurrencies c ON ph.cryptocurrency_id = c.id
WHERE c.symbol IN ('btc', 'eth', 'bnb', 'ada', 'sol')
AND ph.timestamp >= now() - INTERVAL 60 DAY
AND ph.volume_24h > 0
GROUP BY toDate(ph.timestamp)
HAVING total_tvl IS NOT NULL
ORDER BY date DESC
```

**Тип визуализации**: Dual Line Chart  
**Описание**: Сравнение динамики средней цены топ криптовалют с общим TVL в DeFi

---

#### График 10: Топ растущие и падающие активы
```sql
-- Растущие криптовалюты
SELECT 
    'Crypto' as asset_type,
    c.name,
    c.symbol as identifier,
    ph.price_change_percentage_24h as change_24h,
    ph.price_usd as current_value
FROM price_history ph
JOIN cryptocurrencies c ON ph.cryptocurrency_id = c.id
WHERE ph.timestamp >= now() - INTERVAL 1 DAY
AND ph.price_change_percentage_24h > 0
ORDER BY ph.price_change_percentage_24h DESC
LIMIT 10

UNION ALL

-- Растущие DeFi протоколы
SELECT 
    'DeFi' as asset_type,
    dp.name,
    dp.category as identifier,
    th.tvl_change_percentage_24h as change_24h,
    th.tvl as current_value
FROM tvl_history th
JOIN defi_protocols dp ON th.protocol_id = dp.id
WHERE th.timestamp >= now() - INTERVAL 1 DAY
AND th.tvl_change_percentage_24h > 0
ORDER BY th.tvl_change_percentage_24h DESC
LIMIT 10
```

**Тип визуализации**: Table with Conditional Formatting  
**Описание**: Объединенная таблица топ растущих криптовалют и DeFi протоколов

---

## 🎨 Настройка дашбордов

### Создание нового дашборда

1. **Перейдите в Dashboards → "+ DASHBOARD"**
2. **Добавьте название**: "Crypto DeFi Analytics"
3. **Добавьте описание и теги**
4. **Перетащите созданные графики на дашборд**
5. **Настройте фильтры**:
   - Date Range Filter (последние 30 дней)
   - Cryptocurrency Filter (по символу)
   - DeFi Category Filter (по категории)

### Настройка автообновления

1. **В настройках дашборда включите Auto Refresh**
2. **Установите интервал**: 5 минут для production данных
3. **Для разработки**: 30 секунд

### Создание алертов

1. **Перейдите в Alerts & Reports → + ALERT**
2. **Настройте условия**:
   - BTC цена упала на > 10%
   - Total TVL снизился на > 15%
   - Появился новый топ-10 протокол

## 🔧 Продвинутые возможности

### SQL Lab для ad-hoc анализа

```sql
-- Пример: Анализ волатильности криптовалют
SELECT 
    c.name,
    c.symbol,
    stddevPop(ph.price_change_percentage_24h) as volatility,
    avg(ph.price_change_percentage_24h) as avg_change,
    count(*) as data_points
FROM price_history ph
JOIN cryptocurrencies c ON ph.cryptocurrency_id = c.id
WHERE ph.timestamp >= now() - INTERVAL 30 DAY
AND ph.price_change_percentage_24h IS NOT NULL
GROUP BY c.name, c.symbol
HAVING data_points > 10
ORDER BY volatility DESC
LIMIT 20
```

### Создание собственных метрик

```sql
-- Создание индекса страха и жадности для DeFi
SELECT 
    toDate(timestamp) as date,
    -- Компоненты индекса
    avg(tvl_change_percentage_24h) as avg_tvl_change,
    stddevPop(tvl_change_percentage_24h) as tvl_volatility,
    count(case when tvl_change_percentage_24h > 0 then 1 end) * 100.0 / count(*) as positive_ratio,
    
    -- Сводный индекс (0-100, где 0=страх, 100=жадность)
    greatest(0, least(100, 
        50 + avg(tvl_change_percentage_24h) * 2 + 
        (100 - least(100, stddevPop(tvl_change_percentage_24h))) * 0.3 +
        (count(case when tvl_change_percentage_24h > 0 then 1 end) * 100.0 / count(*) - 50)
    )) as defi_sentiment_index
FROM tvl_history
WHERE timestamp >= now() - INTERVAL 30 DAY
AND tvl_change_percentage_24h IS NOT NULL
GROUP BY toDate(timestamp)
ORDER BY date DESC
```

## 🚀 Интеграция с основным приложением

### Встраивание графиков в FastAPI

```python
# В файле templates/analytics.html
<iframe 
    src="http://localhost:8088/superset/dashboard/1/?standalone=3&height=400"
    width="100%" 
    height="400px"
    frameborder="0">
</iframe>
```

### API интеграция

```python
# Получение данных из Superset через API
import requests

def get_superset_data(chart_id):
    url = f"http://localhost:8088/api/v1/chart/{chart_id}/data/"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    response = requests.get(url, headers=headers)
    return response.json()
```

## 📱 Мобильная оптимизация

Все дашборды автоматически адаптируются под мобильные устройства благодаря responsive design Superset.

## 🛠️ Устранение неполадок

### Проблемы подключения к ClickHouse

```bash
# Проверка доступности ClickHouse
docker exec -it crypto-clickhouse clickhouse-client --query "SELECT version()"

# Проверка сети между Superset и ClickHouse
docker exec -it crypto-superset ping clickhouse

# Проверка таблиц в ClickHouse
docker exec -it crypto-clickhouse clickhouse-client --query "SHOW TABLES FROM crypto_analytics"
```

### Первый запуск Superset

```bash
# Просмотр логов инициализации
docker-compose logs -f superset

# Если нужно пересоздать базу Superset
docker-compose down
docker volume rm lab_1_superset_home
docker-compose up superset
```

### Медленные запросы

1. **Добавьте индексы в ClickHouse**:
```sql
-- Для таблицы price_history
ALTER TABLE price_history ADD INDEX idx_crypto_timestamp (cryptocurrency_id, timestamp) TYPE minmax GRANULARITY 1;

-- Для таблицы tvl_history  
ALTER TABLE tvl_history ADD INDEX idx_protocol_timestamp (protocol_id, timestamp) TYPE minmax GRANULARITY 1;
```

2. **Используйте кэширование в Superset** (уже настроено в конфигурации)

### Проблемы с памятью

```bash
# Увеличение лимитов для Superset
docker-compose exec superset bash
export SUPERSET_WORKERS=4
export SUPERSET_WORKER_TIMEOUT=600
```

## 🎯 Практические кейсы использования

### Для трейдеров
- Мониторинг цен и объемов в реальном времени
- Анализ корреляций между активами
- Алерты на критические изменения цен

### Для DeFi аналитиков  
- Отслеживание миграции ликвидности между протоколами
- Анализ доходности различных стратегий
- Мониторинг здоровья DeFi экосистемы

### Для инвесторов
- Долгосрочный анализ трендов
- Оценка рисков и волатильности
- Портфельная аналитика

---

**🎉 Готово!** Теперь у вас есть мощная система аналитики для анализа криптовалютного и DeFi рынков через Apache Superset, интегрированная с вашим проектом Crypto DeFi Analyzer.