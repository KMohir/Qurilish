#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных SFX Savdo Bot
"""

import psycopg2
from config import DB_CONFIG
import sys

def create_database():
    """Создание базы данных и таблиц"""
    try:
        # Подключение к PostgreSQL без указания базы данных
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'  # Подключаемся к системной базе
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Проверяем, существует ли база данных
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            # Создаем базу данных
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            print(f"✅ База данных '{DB_CONFIG['database']}' создана успешно!")
        else:
            print(f"ℹ️ База данных '{DB_CONFIG['database']}' уже существует.")
        
        cursor.close()
        conn.close()
        
        # Теперь подключаемся к созданной базе данных и создаем таблицы
        from database import Database
        db = Database()
        db.create_tables()
        
        print("✅ Инициализация базы данных завершена успешно!")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("Убедитесь, что PostgreSQL запущен и настройки в config.py корректны.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при создании базы данных: {e}")
        sys.exit(1)

def check_connection():
    """Проверка подключения к базе данных"""
    try:
        from database import Database
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"✅ Подключение к базе данных успешно!")
        print(f"PostgreSQL версия: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Инициализация базы данных SFX Savdo Bot")
    print("=" * 50)
    
    # Проверяем подключение
    if check_connection():
        print("\n📊 Создание таблиц...")
        create_database()
    else:
        print("\n❌ Не удалось подключиться к базе данных.")
        print("Проверьте настройки в config.py и убедитесь, что PostgreSQL запущен.")
        sys.exit(1) 