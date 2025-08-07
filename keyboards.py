from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Создать заявку")],
            [KeyboardButton(text="📊 Мои заявки")],
            [KeyboardButton(text="💰 Мои предложения")],
            [KeyboardButton(text="📦 Доставки")],
            [KeyboardButton(text="👤 Профиль")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_role_keyboard():
    """Клавиатура выбора роли"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Заказчик")],
            [KeyboardButton(text="🏪 Поставщик")],
            [KeyboardButton(text="🏭 Зав. Склад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_request_type_keyboard():
    """Клавиатура выбора типа заявки"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Excel файл")],
            [KeyboardButton(text="📝 Текстовый формат")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_offer_type_keyboard():
    """Клавиатура выбора типа предложения"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Excel файл")],
            [KeyboardButton(text="📝 Текстовый формат")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_admin_keyboard():
    """Клавиатура администратора"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Пользователи на одобрении")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_approval_keyboard(user_id):
    """Клавиатура для одобрения пользователя"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{user_id}")
    )
    return keyboard

def get_offer_approval_keyboard(offer_id):
    """Клавиатура для одобрения предложения"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_offer_{offer_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_offer_{offer_id}")
    )
    return keyboard

def get_delivery_keyboard(delivery_id):
    """Клавиатура для подтверждения получения товара"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("✅ Получено", callback_data=f"received_{delivery_id}")
    )
    return keyboard

def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_contact_keyboard():
    """Клавиатура для отправки контакта"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Менинг рақамини юбориш", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_object_keyboard():
    """Клавиатура выбора объекта"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Сам Сити")],
            [KeyboardButton(text="Ситй+Сиёб Б Й К блок")],
            [KeyboardButton(text="Ал Бухорий")],
            [KeyboardButton(text="Ал-Бухорий Хотел")],
            [KeyboardButton(text="Рубловка")],
            [KeyboardButton(text="Қува ҚВП")],
            [KeyboardButton(text="Макон Малл")],
            [KeyboardButton(text="Карши Малл")],
            [KeyboardButton(text="Карши Хотел")],
            [KeyboardButton(text="Воха Гавхари")],
            [KeyboardButton(text="Зарметан усто Ғафур")],
            [KeyboardButton(text="Кожа завод")],
            [KeyboardButton(text="Мотрид катеж")],
            [KeyboardButton(text="Хишрав")],
            [KeyboardButton(text="Махдуми Азам")],
            [KeyboardButton(text="Сирдарё 1/10 Зухри")],
            [KeyboardButton(text="Эшонгузар")],
            [KeyboardButton(text="Рубловка(Хожи бобо дом)")],
            [KeyboardButton(text="Ургут")],
            [KeyboardButton(text="Қўқон малл")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return keyboard 