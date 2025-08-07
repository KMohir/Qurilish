import os
from dotenv import load_dotenv

load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')

# Администраторы (ID пользователей Telegram через запятую)
ADMIN_IDS = [
    int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') 
    if id.strip()
]

# Временная зона
TIMEZONE = 'Asia/Tashkent'

# Настройки базы данных PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'sfx_savdo_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

# Роли пользователей
ROLES = {
    'buyer': 'Заказчик',
    'seller': 'Поставщик', 
    'warehouse': 'Зав. Склад',
    'admin': 'Администратор'
}

# Статусы заявок
REQUEST_STATUSES = {
    'active': 'Активная',
    'completed': 'Завершена',
    'cancelled': 'Отменена'
}

# Статусы предложений
OFFER_STATUSES = {
    'pending': 'Ожидает рассмотрения',
    'approved': 'Одобрено',
    'rejected': 'Отклонено',
    'delivered': 'Доставлено'
}

# Статусы доставки
DELIVERY_STATUSES = {
    'pending': 'Ожидает доставки',
    'received': 'Получено',
    'completed': 'Завершено'
} 