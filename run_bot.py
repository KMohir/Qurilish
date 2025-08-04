#!/usr/bin/env python3
"""
Скрипт для запуска SFX Savdo Bot
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

def check_environment():
    """Проверка переменных окружения"""
    load_dotenv()
    
    required_vars = [
        'BOT_TOKEN',
        'DB_HOST',
        'DB_PORT', 
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        print("Создайте файл .env на основе env_example.txt")
        return False
    
    return True

def check_dependencies():
    """Проверка зависимостей"""
    try:
        import aiogram
        import psycopg2
        import pandas
        import openpyxl
        import pytz
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def check_database():
    """Проверка подключения к базе данных"""
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        conn.close()
        print("✅ Подключение к базе данных успешно")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        print("Запустите: python init_db.py")
        return False

def check_bot_token():
    """Проверка токена бота"""
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    
    if not token or token == 'your_bot_token_here':
        print("❌ Токен бота не настроен")
        print("Получите токен у @BotFather и добавьте в .env файл")
        return False
    
    print("✅ Токен бота настроен")
    return True

async def main():
    """Главная функция"""
    print("🚀 Запуск SFX Savdo Bot")
    print("=" * 40)
    
    # Проверки
    checks = [
        ("Переменные окружения", check_environment),
        ("Зависимости", check_dependencies),
        ("База данных", check_database),
        ("Токен бота", check_bot_token)
    ]
    
    for check_name, check_func in checks:
        print(f"\n🔍 Проверка: {check_name}")
        if not check_func():
            print(f"❌ Проверка '{check_name}' не пройдена")
            sys.exit(1)
    
    print("\n✅ Все проверки пройдены успешно!")
    print("🤖 Запуск бота...")
    
    # Импорт и запуск бота
    try:
        from bot import main as bot_main
        await bot_main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 