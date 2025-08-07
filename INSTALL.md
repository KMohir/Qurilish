# Пошаговая инструкция по установке SFX SAVDO бота

## Шаг 1: Подготовка системы

### Установка Python 3.10.18

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev
```

**CentOS/RHEL:**
```bash
sudo yum install python3.10 python3.10-devel
```

**Windows:**
Скачайте с официального сайта: https://www.python.org/downloads/

### Установка PostgreSQL

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

**Windows:**
Скачайте с официального сайта: https://www.postgresql.org/download/windows/

## Шаг 2: Клонирование проекта

```bash
git clone <repository_url>
cd SFX_SAVDO
```

## Шаг 3: Автоматическая установка

Запустите скрипт установки:

```bash
./setup.sh
```

Или выполните вручную:

```bash
# Создание виртуального окружения
python3.10 -m venv venv

# Активация виртуального окружения
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
cp env_example.txt .env
```

## Шаг 4: Настройка базы данных

### 4.1 Создание базы данных

```bash
# Подключение к PostgreSQL
sudo -u postgres psql

# Создание базы данных и пользователя
CREATE DATABASE sfx_savdo_db;
CREATE USER sfx_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE sfx_savdo_db TO sfx_user;
\q
```

### 4.2 Инициализация таблиц

```bash
# Запуск SQL скрипта
psql -U sfx_user -d sfx_savdo_db -f database.sql
```

## Шаг 5: Настройка бота

### 5.1 Получение токена бота

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Введите имя бота (например: "SFX SAVDO Bot")
4. Введите username бота (например: "sfx_savdo_bot")
5. Скопируйте полученный токен

### 5.2 Настройка переменных окружения

Отредактируйте файл `.env`:

```env
# Токен бота Telegram
BOT_TOKEN=your_actual_bot_token_here

# Настройки базы данных
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sfx_savdo_db
DB_USER=sfx_user
DB_PASSWORD=your_secure_password
```

## Шаг 6: Запуск бота

```bash
# Активация виртуального окружения
source venv/bin/activate

# Запуск бота
python bot.py
```

## Шаг 7: Тестирование

1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Зарегистрируйтесь как продавец (не требует одобрения)
4. Протестируйте создание заявки

## Структура проекта

```
SFX_SAVDO/
├── bot.py              # Основной файл бота
├── config.py           # Конфигурация
├── database.py         # Работа с базой данных
├── handlers.py         # Дополнительные обработчики
├── keyboards.py        # Клавиатуры
├── states.py          # Состояния FSM
├── utils.py           # Утилиты
├── database.sql       # SQL скрипт для создания БД
├── requirements.txt    # Зависимости Python
├── setup.sh           # Скрипт установки
├── env_example.txt    # Пример .env файла
├── README.md          # Документация
└── INSTALL.md         # Эта инструкция
```

## Возможные проблемы и решения

### Проблема: "Python 3.10 не найден"
**Решение:** Установите Python 3.10 согласно инструкции выше

### Проблема: "PostgreSQL не найден"
**Решение:** Установите PostgreSQL согласно инструкции выше

### Проблема: "Ошибка подключения к базе данных"
**Решение:** 
1. Проверьте настройки в `.env` файле
2. Убедитесь, что PostgreSQL запущен: `sudo systemctl status postgresql`
3. Проверьте права доступа пользователя базы данных

### Проблема: "Токен бота недействителен"
**Решение:** 
1. Проверьте токен в `.env` файле
2. Убедитесь, что бот создан через @BotFather
3. Проверьте, что токен скопирован полностью

### Проблема: "Модуль не найден"
**Решение:** 
1. Активируйте виртуальное окружение: `source venv/bin/activate`
2. Установите зависимости: `pip install -r requirements.txt`

## Команды для управления

### Остановка бота
Нажмите `Ctrl+C` в терминале

### Перезапуск бота
```bash
source venv/bin/activate
python bot.py
```

### Просмотр логов
Логи выводятся в консоль. Для сохранения в файл:
```bash
python bot.py > bot.log 2>&1
```

### Обновление зависимостей
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

## Безопасность

1. **Никогда не публикуйте токен бота**
2. **Используйте сложные пароли для базы данных**
3. **Регулярно обновляйте зависимости**
4. **Делайте резервные копии базы данных**

## Поддержка

При возникновении проблем:

1. Проверьте логи в консоли
2. Убедитесь в правильности всех настроек
3. Проверьте подключение к базе данных
4. Убедитесь в корректности токена бота

## Резервное копирование

### Создание резервной копии базы данных
```bash
pg_dump -U sfx_user -d sfx_savdo_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Восстановление из резервной копии
```bash
psql -U sfx_user -d sfx_savdo_db < backup_file.sql
``` 