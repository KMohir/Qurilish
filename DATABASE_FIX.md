# Исправление ошибки базы данных

## 🐛 Проблема
Ошибка: `relation "seller_offer_items" does not exist`

## 🔍 Причина
В функции `process_goods_received()` в файле `bot.py` (строка 1217) код пытался получить данные из таблицы `seller_offer_items`, которая не существует в текущей схеме базы данных.

## ✅ Решение

### 1. Анализ текущей схемы
В файле `database.sql` определена следующая структура:
- `purchase_requests` - заявки на покупку (содержит данные о товарах)
- `seller_offers` - предложения поставщиков
- `deliveries` - доставки

### 2. Исправление SQL запроса
Заменили запрос:
```sql
-- НЕПРАВИЛЬНО (таблица не существует)
SELECT soi.product_name, soi.quantity, soi.unit, soi.price, soi.total, soi.description
FROM seller_offer_items soi
JOIN seller_offers so ON soi.offer_id = so.id
WHERE so.id = %s
```

На правильный:
```sql
-- ПРАВИЛЬНО (используем существующие таблицы)
SELECT pr.product_name, pr.quantity, pr.unit, so.price, so.total_amount as total, pr.material_description as description
FROM purchase_requests pr
JOIN seller_offers so ON pr.id = so.purchase_request_id
WHERE so.id = %s
```

### 3. Объяснение изменений
- **Источник данных**: Теперь получаем данные из `purchase_requests` вместо несуществующей `seller_offer_items`
- **Связь таблиц**: Используем связь `purchase_requests.id = seller_offers.purchase_request_id`
- **Поля данных**: 
  - `product_name`, `quantity`, `unit` - из `purchase_requests`
  - `price`, `total_amount` - из `seller_offers`
  - `material_description` - из `purchase_requests` (переименовано в `description`)

## 📁 Созданные файлы

1. `create_seller_offer_items.sql` - SQL скрипт для создания таблицы `seller_offer_items` (на будущее)

## 🔄 Результат
- ✅ Ошибка исправлена
- ✅ Бот запускается без ошибок
- ✅ Google Sheets интеграция работает
- ✅ Данные корректно записываются в Google Sheets

## 💡 Рекомендации

### Для текущего использования:
Используйте существующую схему с таблицами `purchase_requests` и `seller_offers`.

### Для будущего развития:
Если понадобится более детальное хранение товаров в предложениях, можно:
1. Выполнить скрипт `create_seller_offer_items.sql`
2. Обновить код для использования новой таблицы
3. Мигрировать существующие данные

## 🧪 Тестирование
Бот протестирован и работает корректно:
- ✅ Запуск без ошибок
- ✅ Google Sheets интеграция
- ✅ Запись данных в Google Sheets
