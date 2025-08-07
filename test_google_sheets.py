#!/usr/bin/env python3
"""
Тестовый скрипт для проверки записи данных в Google Sheets
"""

from google_sheets import GoogleSheetsManager

def test_write_delivery_data():
    """Тестирует запись данных о доставке в Google Sheets"""
    
    # Тестовые данные
    test_delivery_data = {
        'date': '07.08.2025',
        'supplier': 'Тестовый поставщик',
        'object': 'Тестовый объект',
        'items': [
            {
                'name': 'Қора қум',
                'quantity': '1.00',
                'unit': 'Рес',
                'price': '4.00 сўм',
                'total': '4.00 сўм',
                'description': '24 м3'
            },
            {
                'name': 'Қора қум',
                'quantity': '1.00',
                'unit': 'Рес',
                'price': '5.00 сўм',
                'total': '5.00 сўм',
                'description': '24 м3'
            },
            {
                'name': 'Қора қум',
                'quantity': '1.00',
                'unit': 'Рес',
                'price': '10.00 сўм',
                'total': '10.00 сўм',
                'description': '24 м3'
            }
        ]
    }
    
    try:
        # Создаем менеджер Google Sheets
        sheets_manager = GoogleSheetsManager()
        
        # Тестируем подключение
        if not sheets_manager.test_connection():
            print("❌ Ошибка подключения к Google Sheets")
            return False
        
        print("✅ Подключение к Google Sheets успешно")
        
        # Записываем тестовые данные
        if sheets_manager.append_delivery_data(test_delivery_data):
            print("✅ Тестовые данные успешно записаны в Google Sheets")
            print(f"📊 Записано {len(test_delivery_data['items'])} товаров")
            return True
        else:
            print("❌ Ошибка записи данных в Google Sheets")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование записи в Google Sheets...")
    success = test_write_delivery_data()
    
    if success:
        print("\n🎉 Тест прошел успешно!")
        print("📋 Проверьте Google Sheets: https://docs.google.com/spreadsheets/d/1w0ZJ7X44AC_GlnlzkytEhZW8-QKsFiaVQPUvn8YmN1E/edit")
    else:
        print("\n❌ Тест не прошел!")
