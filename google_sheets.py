import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self, credentials_file='credentials.json', spreadsheet_id=None):
        """
        Инициализация менеджера Google Sheets
        
        Args:
            credentials_file (str): Путь к файлу с учетными данными
            spreadsheet_id (str): ID таблицы Google Sheets
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id or '1w0ZJ7X44AC_GlnlzkytEhZW8-QKsFiaVQPUvn8YmN1E'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Аутентификация в Google Sheets API"""
        try:
            if not os.path.exists(self.credentials_file):
                logger.error(f"Файл {self.credentials_file} не найден!")
                return False
            
            # Области доступа для Google Sheets API
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загружаем учетные данные
            credentials = Credentials.from_service_account_file(
                self.credentials_file, 
                scopes=SCOPES
            )
            
            # Создаем сервис
            self.service = build('sheets', 'v4', credentials=credentials)
            logger.info("Успешная аутентификация в Google Sheets API")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            return False
    
    def append_delivery_data(self, delivery_data):
        """
        Добавляет данные о доставке в Google Sheets
        
        Args:
            delivery_data (dict): Словарь с данными о доставке
                {
                    'supplier': 'Поставщик',
                    'object': 'Объект',
                    'items': [
                        {
                            'name': 'Название товара',
                            'quantity': 'Количество',
                            'unit': 'Единица измерения',
                            'price': 'Цена',
                            'total': 'Сумма',
                            'description': 'Описание'
                        }
                    ]
                }
        """
        if not self.service:
            logger.error("Сервис Google Sheets не инициализирован")
            return False
        
        try:
            # Подготавливаем данные для записи
            rows = []
            
            for item in delivery_data['items']:
                # Преобразуем количество в int (убираем .00)
                quantity = item['quantity']
                if quantity and '.' in quantity:
                    try:
                        quantity = str(int(float(quantity)))
                    except:
                        pass
                
                # Убираем "сўм" из цены и суммы
                price = item['price'].replace(' сўм', '').replace(' сум', '') if item['price'] else ''
                total = item['total'].replace(' сўм', '').replace(' сум', '') if item['total'] else ''
                
                row = [
                    delivery_data['date'],       # A: Дата (Кун)
                    delivery_data['supplier'],   # B: Поставщик (Потсавшик)
                    delivery_data['object'],     # C: Объект номи
                    item['name'],                # D: Махсулот номи
                    quantity,                    # E: Миқдори
                    item['unit'],                # F: Ўлчов бирлиги
                    item['description'],         # G: Материал изох
                    price,                       # H: Нархи
                    total                        # I: Суммаси
                ]
                rows.append(row)
            
            # Диапазон для записи (Лист1) - расширен до колонки I
            range_name = 'Лист1!A:I'
            
            # Записываем данные
            body = {
                'values': rows
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Данные успешно записаны в Google Sheets: {len(rows)} строк")
            return True
            
        except HttpError as e:
            logger.error(f"Ошибка записи в Google Sheets: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return False
    
    def test_connection(self):
        """Тестирует подключение к Google Sheets"""
        try:
            if not self.service:
                return False
            
            # Пытаемся прочитать заголовки таблицы
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Лист1!A1:H1'
            ).execute()
            
            logger.info("Подключение к Google Sheets успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            return False

# Функция для парсинга сообщения о доставке
def parse_delivery_message(message_text):
    """
    Парсит сообщение о доставке и извлекает данные
    
    Args:
        message_text (str): Текст сообщения о доставке
        
    Returns:
        dict: Словарь с данными о доставке
    """
    try:
        lines = message_text.split('\n')
        delivery_data = {
            'supplier': '',
            'object': '',
            'items': []
        }
        
        current_item = None
        
        for line in lines:
            line = line.strip()
            
            # Извлекаем поставщика
            if line.startswith('👤 Поставщик:'):
                delivery_data['supplier'] = line.replace('👤 Поставщик:', '').strip()
            
            # Извлекаем объект
            elif line.startswith('🏗️ Объект:'):
                delivery_data['object'] = line.replace('🏗️ Объект:', '').strip()
            
            # Начинаем новый товар
            elif line.startswith('**') and line.endswith('**'):
                if current_item:
                    delivery_data['items'].append(current_item)
                
                current_item = {
                    'name': line.replace('**', '').strip(),
                    'quantity': '',
                    'unit': '',
                    'price': '',
                    'total': '',
                    'description': ''
                }
            
            # Извлекаем данные товара
            elif current_item:
                if line.startswith('📊 Миқдори:'):
                    parts = line.replace('📊 Миқдори:', '').strip().split()
                    if len(parts) >= 2:
                        current_item['quantity'] = parts[0]
                        current_item['unit'] = parts[1]
                
                elif line.startswith('💰 Нархи:'):
                    current_item['price'] = line.replace('💰 Нархи:', '').strip()
                
                elif line.startswith('💵 Сумма:'):
                    current_item['total'] = line.replace('💵 Сумма:', '').strip()
                
                elif line.startswith('📝 Изох:'):
                    current_item['description'] = line.replace('📝 Изох:', '').strip()
        
        # Добавляем последний товар
        if current_item:
            delivery_data['items'].append(current_item)
        
        return delivery_data
        
    except Exception as e:
        logger.error(f"Ошибка парсинга сообщения: {e}")
        return None

# Пример использования
if __name__ == "__main__":
    # Тестирование подключения
    sheets_manager = GoogleSheetsManager()
    if sheets_manager.test_connection():
        print("Подключение к Google Sheets успешно!")
    else:
        print("Ошибка подключения к Google Sheets!")
