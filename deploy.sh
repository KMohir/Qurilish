#!/bin/bash

# 🚀 SFX Savdo Bot - Автоматический скрипт развертывания
# Использование: ./deploy.sh

set -e  # Остановка при ошибке

echo "🚀 Начинаем развертывание SFX Savdo Bot..."

# Проверка прав администратора
if [ "$EUID" -ne 0 ]; then
    echo "❌ Этот скрипт должен выполняться с правами администратора (sudo)"
    exit 1
fi

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Шаг 1: Обновление системы
log "📦 Обновление системы..."
apt update && apt upgrade -y

# Шаг 2: Установка необходимых пакетов
log "🔧 Установка необходимых пакетов..."
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib git nginx supervisor curl wget

# Шаг 3: Настройка PostgreSQL
log "🗄️ Настройка PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Создание пользователя базы данных
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='sfx_user'" | grep -q 1; then
    sudo -u postgres createuser --interactive sfx_user
fi

# Создание базы данных
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw sfx_savdo_db; then
    sudo -u postgres createdb sfx_savdo_db
fi

# Установка пароля для пользователя (замените на свой пароль)
echo "Введите пароль для пользователя базы данных sfx_user:"
read -s DB_PASSWORD
sudo -u postgres psql -c "ALTER USER sfx_user WITH PASSWORD '$DB_PASSWORD';"

# Шаг 4: Создание пользователя для бота
log "👤 Создание пользователя для бота..."
if ! id "sfx_user" &>/dev/null; then
    useradd -r -s /bin/false sfx_user
fi

# Шаг 5: Развертывание кода
log "📁 Развертывание кода..."
if [ ! -d "/opt/SFX_SAVDO" ]; then
    mkdir -p /opt
    cd /opt
    git clone https://github.com/your-username/SFX_SAVDO.git
fi

chown -R sfx_user:sfx_user /opt/SFX_SAVDO
cd /opt/SFX_SAVDO

# Шаг 6: Создание виртуального окружения
log "🐍 Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Шаг 7: Создание файла .env
log "⚙️ Создание конфигурации..."
echo "Введите токен Telegram бота:"
read BOT_TOKEN

echo "Введите ID администраторов (через запятую):"
read ADMIN_IDS

cat > .env << EOF
# Telegram Bot
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sfx_savdo_db
DB_USER=sfx_user
DB_PASSWORD=$DB_PASSWORD

# Timezone
TIMEZONE=Asia/Tashkent

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/sfx_bot/bot.log
EOF

chown sfx_user:sfx_user .env

# Шаг 8: Создание директории для логов
log "📊 Создание директории для логов..."
mkdir -p /var/log/sfx_bot
chown sfx_user:sfx_user /var/log/sfx_bot

# Шаг 9: Создание systemd сервиса
log "🔄 Создание systemd сервиса..."
cat > /etc/systemd/system/sfx-bot.service << EOF
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
StandardOutput=append:/var/log/sfx_bot/bot.log
StandardError=append:/var/log/sfx_bot/bot.log

[Install]
WantedBy=multi-user.target
EOF

# Шаг 10: Создание скрипта мониторинга
log "📈 Создание скрипта мониторинга..."
cat > /opt/SFX_SAVDO/monitor.sh << 'EOF'
#!/bin/bash

# Проверка статуса бота
if ! systemctl is-active --quiet sfx-bot; then
    echo "$(date): SFX Bot is down, restarting..." >> /var/log/sfx_bot/monitor.log
    systemctl restart sfx-bot
fi

# Проверка размера логов
if [ -f /var/log/sfx_bot/bot.log ]; then
    LOG_SIZE=$(du -m /var/log/sfx_bot/bot.log | cut -f1)
    if [ $LOG_SIZE -gt 100 ]; then
        echo "$(date): Log file too large, rotating..." >> /var/log/sfx_bot/monitor.log
        mv /var/log/sfx_bot/bot.log /var/log/sfx_bot/bot.log.old
        systemctl restart sfx-bot
    fi
fi
EOF

chmod +x /opt/SFX_SAVDO/monitor.sh

# Шаг 11: Настройка автозапуска
log "🚀 Настройка автозапуска..."
systemctl daemon-reload
systemctl enable sfx-bot

# Шаг 12: Настройка firewall
log "🔒 Настройка firewall..."
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Шаг 13: Добавление мониторинга в crontab
log "⏰ Настройка мониторинга..."
(crontab -u sfx_user -l 2>/dev/null; echo "*/5 * * * * /opt/SFX_SAVDO/monitor.sh") | crontab -u sfx_user -

# Шаг 14: Запуск сервиса
log "🎯 Запуск сервиса..."
systemctl start sfx-bot

# Шаг 15: Проверка статуса
log "✅ Проверка статуса..."
sleep 3

if systemctl is-active --quiet sfx-bot; then
    log "🎉 SFX Savdo Bot успешно развернут и запущен!"
    echo ""
    echo "📊 Статус сервиса:"
    systemctl status sfx-bot --no-pager -l
    echo ""
    echo "📋 Полезные команды:"
    echo "  • Статус: sudo systemctl status sfx-bot"
    echo "  • Логи: sudo journalctl -u sfx-bot -f"
    echo "  • Перезапуск: sudo systemctl restart sfx-bot"
    echo "  • Остановка: sudo systemctl stop sfx-bot"
    echo ""
    echo "📁 Файлы:"
    echo "  • Конфигурация: /opt/SFX_SAVDO/.env"
    echo "  • Логи: /var/log/sfx_bot/bot.log"
    echo "  • База данных: sfx_savdo_db"
    echo ""
    echo "🔧 Для обновления бота выполните:"
    echo "  cd /opt/SFX_SAVDO && git pull && sudo systemctl restart sfx-bot"
else
    error "❌ Ошибка запуска сервиса!"
    echo "Проверьте логи: sudo journalctl -u sfx-bot -f"
    exit 1
fi 