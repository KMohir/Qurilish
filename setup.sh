#!/bin/bash

echo "🚀 Установка SFX SAVDO бота..."

# Проверка наличия Python 3.10
if ! command -v python3.10 &> /dev/null; then
    echo "❌ Python 3.10 не найден. Установите Python 3.10 и попробуйте снова."
    exit 1
fi

# Проверка наличия PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL не найден. Установите PostgreSQL и попробуйте снова."
    echo "Для Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "Для CentOS/RHEL: sudo yum install postgresql postgresql-server"
    exit 1
fi

# Создание виртуального окружения
echo "📦 Создание виртуального окружения..."
python3.10 -m venv venv

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📚 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Создание .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла..."
    cp env_example.txt .env
    echo "✅ Файл .env создан. Отредактируйте его с вашими настройками."
else
    echo "✅ Файл .env уже существует."
fi

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте файл .env с вашими настройками"
echo "2. Создайте базу данных PostgreSQL:"
echo "   sudo -u postgres psql"
echo "   CREATE DATABASE sfx_savdo_db;"
echo "   CREATE USER sfx_user WITH PASSWORD 'your_password';"
echo "   GRANT ALL PRIVILEGES ON DATABASE sfx_savdo_db TO sfx_user;"
echo "   \q"
echo "3. Инициализируйте таблицы:"
echo "   psql -U sfx_user -d sfx_savdo_db -f database.sql"
echo "4. Запустите бота:"
echo "   source venv/bin/activate"
echo "   python bot.py"
echo ""
echo "📖 Подробная документация в файле README.md" 