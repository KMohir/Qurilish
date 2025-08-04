# 🚀 Инструкция по развертыванию SFX Savdo Bot

## 📋 Требования к серверу

### Минимальные требования:
- **ОС:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM:** 2 GB
- **CPU:** 1 ядро
- **Диск:** 20 GB
- **Python:** 3.8+

### Рекомендуемые требования:
- **ОС:** Ubuntu 22.04 LTS
- **RAM:** 4 GB
- **CPU:** 2 ядра
- **Диск:** 50 GB SSD

## 🔧 Шаг 1: Подготовка сервера

### 1.1 Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Установка необходимых пакетов
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git nginx supervisor
```

### 1.3 Настройка PostgreSQL
```bash
# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание пользователя базы данных
sudo -u postgres createuser --interactive sfx_user
sudo -u postgres createdb sfx_savdo_db

# Установка пароля для пользователя
sudo -u postgres psql
ALTER USER sfx_user WITH PASSWORD 'your_secure_password';
\q
```

## 📁 Шаг 2: Развертывание кода

### 2.1 Клонирование репозитория
```bash
cd /opt
sudo git clone https://github.com/your-username/SFX_SAVDO.git
sudo chown -R $USER:$USER /opt/SFX_SAVDO
cd SFX_SAVDO
```

### 2.2 Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 Создание файла requirements.txt
```bash
# Создайте файл requirements.txt со следующим содержимым:
cat > requirements.txt << EOF
aiogram==3.4.1
psycopg2-binary==2.9.9
pandas==2.1.4
openpyxl==3.1.2
python-dotenv==1.0.0
asyncio==3.4.3
EOF
```

## ⚙️ Шаг 3: Настройка конфигурации

### 3.1 Создание файла .env
```bash
cat > .env << EOF
# Telegram Bot
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sfx_savdo_db
DB_USER=sfx_user
DB_PASSWORD=your_secure_password

# Timezone
TIMEZONE=Asia/Tashkent

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/sfx_bot/bot.log
EOF
```

### 3.2 Обновление config.py
```python
# Убедитесь, что config.py использует переменные окружения:
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'sfx_savdo_db'),
    'user': os.getenv('DB_USER', 'sfx_user'),
    'password': os.getenv('DB_PASSWORD', '')
}
```

## 🔄 Шаг 4: Настройка автозапуска

### 4.1 Создание systemd сервиса
```bash
sudo tee /etc/systemd/system/sfx-bot.service > /dev/null << EOF
[Unit]
Description=SFX Savdo Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=sfx_user
Group=sfx_user
WorkingDirectory=/opt/SFX_SAVDO
Environment=PATH=/opt/SFX_SAVDO/venv/bin
ExecStart=/opt/SFX_SAVDO/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 4.2 Создание пользователя для бота
```bash
sudo useradd -r -s /bin/false sfx_user
sudo chown -R sfx_user:sfx_user /opt/SFX_SAVDO
```

### 4.3 Создание директории для логов
```bash
sudo mkdir -p /var/log/sfx_bot
sudo chown sfx_user:sfx_user /var/log/sfx_bot
```

### 4.4 Активация сервиса
```bash
sudo systemctl daemon-reload
sudo systemctl enable sfx-bot
sudo systemctl start sfx-bot
```

## 🌐 Шаг 5: Настройка Nginx (опционально)

### 5.1 Создание конфигурации Nginx
```bash
sudo tee /etc/nginx/sites-available/sfx-bot > /dev/null << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
```

### 5.2 Активация сайта
```bash
sudo ln -s /etc/nginx/sites-available/sfx-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 Шаг 6: Настройка безопасности

### 6.1 Настройка firewall
```bash
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 6.2 Настройка SSL (опционально)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 📊 Шаг 7: Мониторинг и логи

### 7.1 Проверка статуса сервиса
```bash
sudo systemctl status sfx-bot
```

### 7.2 Просмотр логов
```bash
# Логи systemd
sudo journalctl -u sfx-bot -f

# Логи приложения
tail -f /var/log/sfx_bot/bot.log
```

### 7.3 Создание скрипта мониторинга
```bash
cat > /opt/SFX_SAVDO/monitor.sh << 'EOF'
#!/bin/bash

# Проверка статуса бота
if ! systemctl is-active --quiet sfx-bot; then
    echo "$(date): SFX Bot is down, restarting..." >> /var/log/sfx_bot/monitor.log
    systemctl restart sfx-bot
fi

# Проверка размера логов
LOG_SIZE=$(du -m /var/log/sfx_bot/bot.log | cut -f1)
if [ $LOG_SIZE -gt 100 ]; then
    echo "$(date): Log file too large, rotating..." >> /var/log/sfx_bot/monitor.log
    mv /var/log/sfx_bot/bot.log /var/log/sfx_bot/bot.log.old
    systemctl restart sfx-bot
fi
EOF

chmod +x /opt/SFX_SAVDO/monitor.sh
```

### 7.4 Добавление в crontab
```bash
# Добавить в crontab для автоматического мониторинга
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/SFX_SAVDO/monitor.sh") | crontab -
```

## 🚀 Шаг 8: Запуск и тестирование

### 8.1 Первый запуск
```bash
# Активация виртуального окружения
cd /opt/SFX_SAVDO
source venv/bin/activate

# Тестовый запуск
python bot.py
```

### 8.2 Проверка работы
```bash
# Проверка статуса
sudo systemctl status sfx-bot

# Проверка логов
tail -f /var/log/sfx_bot/bot.log

# Проверка базы данных
sudo -u postgres psql -d sfx_savdo_db -c "\dt"
```

## 🔧 Полезные команды

### Управление сервисом
```bash
# Запуск
sudo systemctl start sfx-bot

# Остановка
sudo systemctl stop sfx-bot

# Перезапуск
sudo systemctl restart sfx-bot

# Статус
sudo systemctl status sfx-bot

# Логи
sudo journalctl -u sfx-bot -f
```

### Обновление бота
```bash
cd /opt/SFX_SAVDO
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart sfx-bot
```

### Резервное копирование базы данных
```bash
# Создание бэкапа
sudo -u postgres pg_dump sfx_savdo_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление
sudo -u postgres psql sfx_savdo_db < backup_file.sql
```

## ⚠️ Важные замечания

1. **Безопасность:** Всегда используйте сильные пароли
2. **Обновления:** Регулярно обновляйте систему и зависимости
3. **Мониторинг:** Настройте алерты при падении сервиса
4. **Резервное копирование:** Регулярно создавайте бэкапы базы данных
5. **Логи:** Мониторьте размер логов и ротируйте их при необходимости

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u sfx-bot -f`
2. Проверьте статус сервиса: `sudo systemctl status sfx-bot`
3. Проверьте подключение к базе данных
4. Убедитесь, что токен бота корректный 