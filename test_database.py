#!/usr/bin/env python3
"""
Скрипт для тестирования создания всех таблиц в базе данных
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Database

def test_database_creation():
    """Тестирование создания всех таблиц"""
    print("🔧 Тестирование создания таблиц базы данных...")
    
    try:
        # Создаем экземпляр базы данных
        db = Database()
        
        # Создаем все таблицы
        db.create_tables()
        
        print("✅ Все таблицы успешно созданы!")
        
        # Проверяем подключение к базе данных
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Получаем список всех таблиц
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Созданные таблицы ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_database_creation()
    sys.exit(0 if success else 1)
