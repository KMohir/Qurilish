# 🚀 Быстрый запуск SFX Savdo Bot

## Шаг 1: Подготовка окружения

```bash
# Активация виртуального окружения
source venv_new_new/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

## Шаг 2: Настройка базы данных PostgreSQL

### Установка PostgreSQL (если не установлен):

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**CentOS/RHEL:**
```bash
sudo yum install postgresql postgresql-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Создание базы данных:
```bash
# Подключение к PostgreSQL
sudo -u postgres psql

# В psql выполните:
CREATE DATABASE sfx_savdo_db;
CREATE USER sfx_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sfx_savdo_db TO sfx_user;
\q
```

## Шаг 3: Настройка переменных окружения

```bash
# Копируем пример файла
cp env_example.txt .env

# Редактируем файл .env
nano .env
```

Содержимое файла `.env`:
```env
BOT_TOKEN=your_bot_token_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sfx_savdo_db
DB_USER=sfx_user
DB_PASSWORD=your_password
ADMIN_IDS=123456789
```

## Шаг 4: Получение токена бота

1. Найдите @BotFather в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен в `.env`

## Шаг 5: Получение ID администратора

1. Найдите @userinfobot в Telegram
2. Отправьте любое сообщение
3. Скопируйте ваш ID в переменную `ADMIN_IDS`

## Шаг 6: Инициализация базы данных

```bash
python init_db.py
```

## Шаг 7: Запуск бота

```bash
python run_bot.py
```

## ✅ Проверка работы

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Отправьте `/register`
4. Выберите роль "Продавец" (автоматическое одобрение)
5. Проверьте работу меню

## 🔧 Администрирование

### Добавление покупателя:
1. Пользователь отправляет `/register`
2. Выбирает "Покупатель"
3. Администратор одобряет: `/approve <telegram_id>`

### Добавление человека на складе:
1. Пользователь отправляет `/register`
2. Выбирает "Человек на складе"
3. Администратор одобряет: `/approve <telegram_id>`

### Панель администратора:
```
/admin
```

## 🛠️ Устранение проблем

### Ошибка подключения к базе данных:
```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Перезапустите если нужно
sudo systemctl restart postgresql
```

### Ошибка зависимостей:
```bash
pip install --upgrade -r requirements.txt
```

### Бот не отвечает:
1. Проверьте токен в `.env`
2. Убедитесь, что бот не заблокирован
3. Проверьте логи в консоли

## 📞 Поддержка

При проблемах:
1. Проверьте логи в консоли
2. Убедитесь в правильности настроек
3. Проверьте подключение к базе данных 