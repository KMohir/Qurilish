import pandas as pd
import io
from datetime import datetime
import pytz

def get_uzbek_time():
    """Получение текущего времени в Узбекистане"""
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)

def format_uzbek_time():
    """Форматирование времени в узбекском формате"""
    uzbek_time = get_uzbek_time()
    return uzbek_time.strftime("%d.%m.%Y %H:%M")

def create_excel_template():
    """Создание шаблона Excel для заявок на покупку"""
    df = pd.DataFrame(columns=[
        'Заказчик',
        'Поставщик', 
        'Объект номи',
        'Махсулот номи',
        'Миқдори',
        'Ўлчов бирлиги',
        'Материал изох'
    ])
    
    # Создание Excel файла в памяти
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Заявка')
    
    output.seek(0)
    return output

def create_offer_excel_template():
    """Создание шаблона Excel для предложений поставщиков"""
    df = pd.DataFrame(columns=[
        'Нархи',
        'Суммаси'
    ])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Предложение')
    
    output.seek(0)
    return output

def parse_excel_request(file_content):
    """Парсинг Excel файла с заявкой на покупку"""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        requests = []
        
        for _, row in df.iterrows():
            if pd.notna(row['Заказчик']):  # Проверяем, что строка не пустая
                request = {
                    'buyer': row.get('Заказчик', ''),
                    'supplier': row.get('Поставщик', ''),
                    'object_name': row.get('Объект номи', ''),
                    'product_name': row.get('Махсулот номи', ''),
                    'quantity': row.get('Миқдори', 0),
                    'unit': row.get('Ўлчов бирлиги', ''),
                    'material_description': row.get('Материал изох', '')
                }
                requests.append(request)
        
        return requests
    except Exception as e:
        raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")

def parse_excel_offer(file_content):
    """Парсинг Excel файла с предложением поставщика"""
    try:
        df = pd.read_excel(io.BytesIO(file_content))
        offers = []
        
        for _, row in df.iterrows():
            if pd.notna(row['Нархи']):  # Проверяем, что строка не пустая
                offer = {
                    'price': row.get('Нархи', 0),
                    'total_amount': row.get('Суммаси', 0)
                }
                offers.append(offer)
        
        return offers
    except Exception as e:
        raise ValueError(f"Ошибка при чтении Excel файла: {str(e)}")

def validate_phone_number(phone):
    """Валидация номера телефона"""
    import re
    # Убираем все пробелы и символы
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Проверяем узбекские форматы
    if phone.startswith('+998') and len(phone) == 13:
        return phone
    elif phone.startswith('998') and len(phone) == 12:
        return '+' + phone
    elif phone.startswith('0') and len(phone) == 9:
        return '+998' + phone
    else:
        return None

def format_request_text(request_data):
    """Форматирование текста заявки"""
    text = f"""
📋 **Заявка на покупку**

👤 **Заказчик:** {request_data.get('buyer', 'Не указан')}
🏢 **Поставщик:** {request_data.get('supplier', 'Не указан')}
🏗️ **Объект:** {request_data.get('object_name', 'Не указан')}
📦 **Товар:** {request_data.get('product_name', 'Не указан')}
📊 **Количество:** {request_data.get('quantity', 0)} {request_data.get('unit', '')}
📝 **Описание:** {request_data.get('material_description', 'Не указано')}

⏰ **Время создания:** {format_uzbek_time()}
"""
    return text

def format_offer_text(offer_data, seller_name, seller_phone):
    """Форматирование текста предложения"""
    text = f"""
💰 **Предложение поставщика**

👤 **Поставщик:** {seller_name}
📞 **Телефон:** {seller_phone}
💵 **Цена:** {offer_data.get('price', 0)} сум
💸 **Сумма:** {offer_data.get('total_amount', 0)} сум

⏰ **Время предложения:** {format_uzbek_time()}
"""
    return text 