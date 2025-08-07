# Автоматическое создание таблиц базы данных

## Обзор

Все таблицы базы данных теперь создаются автоматически при запуске бота. Это означает, что вам не нужно вручную выполнять SQL скрипты для создания таблиц.

## Как это работает

### 1. Функция `create_tables()`

В файле `database.py` есть функция `create_tables()`, которая создает все необходимые таблицы:

```python
def create_tables(self):
    """Создание всех необходимых таблиц"""
    # Создает все таблицы с помощью CREATE TABLE IF NOT EXISTS
```

### 2. Автоматический вызов

Функция `create_tables()` вызывается автоматически в функции `main()` в файле `bot.py`:

```python
async def main():
    """Главная функция"""
    # Создание таблиц базы данных
    db.create_tables()
    
    # Запуск бота
    await dp.start_polling(bot)
```

### 3. Создаваемые таблицы

При запуске бота автоматически создаются следующие таблицы:

1. **`users`** - Пользователи системы
   - `id` (SERIAL PRIMARY KEY)
   - `telegram_id` (BIGINT UNIQUE)
   - `username` (VARCHAR(255))
   - `full_name` (VARCHAR(255))
   - `phone_number` (VARCHAR(20))
   - `role` (VARCHAR(20)) - buyer, seller, warehouse, admin
   - `object_name` (VARCHAR(255))
   - `location` (VARCHAR(500))
   - `is_approved` (BOOLEAN)
   - `created_at` (TIMESTAMP)

2. **`purchase_requests`** - Заявки заказчиков
   - `id` (SERIAL PRIMARY KEY)
   - `buyer_id` (INTEGER REFERENCES users(id))
   - `supplier` (VARCHAR(255))
   - `object_name` (VARCHAR(255))
   - `request_type` (VARCHAR(10)) - excel, text
   - `status` (VARCHAR(20)) - active, completed, cancelled
   - `created_at` (TIMESTAMP)

3. **`request_items`** - Товары в заявках
   - `id` (SERIAL PRIMARY KEY)
   - `request_id` (INTEGER REFERENCES purchase_requests(id))
   - `product_name` (VARCHAR(255))
   - `quantity` (DECIMAL(15,2))
   - `unit` (VARCHAR(50))
   - `material_description` (TEXT)
   - `created_at` (TIMESTAMP)

4. **`seller_offers`** - Предложения поставщиков
   - `id` (SERIAL PRIMARY KEY)
   - `purchase_request_id` (INTEGER REFERENCES purchase_requests(id))
   - `seller_id` (INTEGER REFERENCES users(id))
   - `total_amount` (DECIMAL(15,2))
   - `offer_type` (VARCHAR(10)) - excel, text
   - `status` (VARCHAR(20)) - pending, approved, rejected, delivered
   - `excel_filename` (VARCHAR(255))
   - `created_at` (TIMESTAMP)

5. **`offer_items`** - Товары в предложениях (старая таблица)
   - `id` (SERIAL PRIMARY KEY)
   - `offer_id` (INTEGER REFERENCES seller_offers(id))
   - `product_name` (VARCHAR(255))
   - `quantity` (DECIMAL(15,2))
   - `unit` (VARCHAR(50))
   - `price_per_unit` (DECIMAL(15,2))
   - `total_price` (DECIMAL(15,2))
   - `material_description` (TEXT)
   - `created_at` (TIMESTAMP)

6. **`seller_offer_items`** - Товары в предложениях (новая таблица)
   - `id` (SERIAL PRIMARY KEY)
   - `offer_id` (INTEGER REFERENCES seller_offers(id))
   - `product_name` (VARCHAR(255))
   - `quantity` (DECIMAL(15,2))
   - `unit` (VARCHAR(50))
   - `price` (DECIMAL(15,2))
   - `total` (DECIMAL(15,2))
   - `description` (TEXT)
   - `created_at` (TIMESTAMP)

7. **`deliveries`** - Доставки
   - `id` (SERIAL PRIMARY KEY)
   - `offer_id` (INTEGER REFERENCES seller_offers(id))
   - `warehouse_user_id` (INTEGER REFERENCES users(id))
   - `buyer_id` (INTEGER REFERENCES users(id))
   - `status` (VARCHAR(20)) - pending, delivered, received
   - `received_at` (TIMESTAMP)
   - `created_at` (TIMESTAMP)

## Дополнительные функции

### `fix_decimal_fields()`

Автоматически исправляет типы полей для поддержки больших чисел:

```python
def fix_decimal_fields(self):
    """Исправление типов полей для поддержки больших чисел"""
    # Изменяет типы полей на DECIMAL(15,2)
```

### `add_missing_columns()`

Автоматически добавляет недостающие колонки в существующие таблицы:

```python
def add_missing_columns(self):
    """Добавление недостающих колонок в таблицы"""
    # Добавляет object_name и location в users
    # Создает seller_offer_items если не существует
```

## Тестирование

Для проверки создания таблиц можно использовать скрипт `test_database.py`:

```bash
python test_database.py
```

Этот скрипт:
1. Создает все таблицы
2. Выводит список созданных таблиц
3. Проверяет подключение к базе данных

## Преимущества

1. **Автоматизация**: Не нужно вручную создавать таблицы
2. **Безопасность**: Используется `CREATE TABLE IF NOT EXISTS`
3. **Гибкость**: Легко добавлять новые таблицы и колонки
4. **Совместимость**: Поддерживает обновление существующих баз данных
5. **Отладка**: Подробное логирование процесса создания

## Миграции

При добавлении новых таблиц или колонок:

1. Добавьте создание таблицы в `create_tables()`
2. Добавьте исправление типов в `fix_decimal_fields()` (если нужно)
3. Добавьте создание таблицы в `add_missing_columns()` (если нужно)
4. Обновите документацию

## Пример добавления новой таблицы

```python
# В функции create_tables()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# В функции fix_decimal_fields() (если есть числовые поля)
fixes.append(("new_table", "amount", "DECIMAL(15,2)"))

# В функции add_missing_columns() (для обратной совместимости)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
```
