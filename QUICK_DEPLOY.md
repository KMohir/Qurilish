# 🚀 Быстрое развертывание SFX Savdo Bot

## ⚡ Быстрый старт (5 минут)

### 1. Подготовка сервера
```bash
# Подключитесь к серверу и выполните:
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl
```

### 2. Клонирование проекта
```bash
cd /opt
sudo git clone https://github.com/your-username/SFX_SAVDO.git
sudo chown -R $USER:$USER /opt/SFX_SAVDO
cd SFX_SAVDO
```

### 3. Автоматическое развертывание
```bash
# Запустите автоматический скрипт
sudo ./deploy.sh
```

### 4. Настройка конфигурации
Скрипт попросит ввести:
- **Токен Telegram бота** (получите у @BotFather)
- **ID администраторов** (ваш Telegram ID)
- **Пароль для базы данных**

## 🔧 Ручное развертывание

### Шаг 1: Установка зависимостей
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib
```

### Шаг 2: Настройка базы данных
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
sudo -u postgres createuser sfx_user
sudo -u postgres createdb sfx_savdo_db
sudo -u postgres psql -c "ALTER USER sfx_user WITH PASSWORD 'your_password';"
```

### Шаг 3: Установка Python зависимостей
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Шаг 4: Создание конфигурации
```bash
cat > .env << EOF
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sfx_savdo_db
DB_USER=sfx_user
DB_PASSWORD=your_password
TIMEZONE=Asia/Tashkent
EOF
```

### Шаг 5: Запуск
```bash
python bot.py
```

## 📋 Проверка работы

### Статус сервиса
```bash
sudo systemctl status sfx-bot
```

### Просмотр логов
```bash
sudo journalctl -u sfx-bot -f
```

### Проверка базы данных
```bash
sudo -u postgres psql -d sfx_savdo_db -c "\dt"
```

## 🔄 Обновление

### Автоматическое обновление
```bash
cd /opt/SFX_SAVDO
git pull
sudo systemctl restart sfx-bot
```

### Ручное обновление
```bash
cd /opt/SFX_SAVDO
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sfx-bot
```

## 🆘 Устранение неполадок

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u sfx-bot -f

# Проверьте конфигурацию
cat /opt/SFX_SAVDO/.env

# Проверьте базу данных
sudo -u postgres psql -d sfx_savdo_db -c "SELECT version();"
```

### Ошибки базы данных
```bash
# Перезапуск PostgreSQL
sudo systemctl restart postgresql

# Проверка подключения
sudo -u postgres psql -d sfx_savdo_db
```

### Проблемы с правами
```bash
# Исправление прав доступа
sudo chown -R sfx_user:sfx_user /opt/SFX_SAVDO
sudo chown sfx_user:sfx_user /var/log/sfx_bot
```

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u sfx-bot -f`
2. Убедитесь, что токен бота корректный
3. Проверьте подключение к базе данных
4. Проверьте права доступа к файлам

## 🎯 Готово!

После успешного развертывания:
- ✅ Бот автоматически запускается при старте сервера
- ✅ Автоматический перезапуск при сбоях
- ✅ Ротация логов
- ✅ Мониторинг состояния
- ✅ Резервное копирование (настройте отдельно) 