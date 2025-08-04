import asyncio
import logging
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, ADMIN_IDS, TIMEZONE
from database import Database
import pandas as pd
import io
import psycopg2.extras

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Инициализация базы данных
db = Database()

# Состояния FSM
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_role = State()

class PurchaseRequestStates(StatesGroup):
    waiting_for_supplier = State()
    waiting_for_object = State()
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_unit = State()
    waiting_for_description = State()

class SellerOfferStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_total = State()

# Временная зона
timezone = pytz.timezone(TIMEZONE)

def is_admin(user_id: int) -> bool:
    """Проверка является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def get_current_time():
    """Получение текущего времени в узбекской временной зоне"""
    return datetime.now(timezone).strftime("%d.%m.%Y %H:%M")

# Клавиатуры
def get_main_keyboard(user_role: str):
    """Главная клавиатура в зависимости от роли"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_role == 'buyer':
        keyboard.add(KeyboardButton("📋 Создать заявку"))
        keyboard.add(KeyboardButton("📊 Мои заявки"))
        keyboard.add(KeyboardButton("📦 Мои заказы"))
    elif user_role == 'seller':
        keyboard.add(KeyboardButton("📋 Активные заявки"))
        keyboard.add(KeyboardButton("💼 Мои предложения"))
    elif user_role == 'warehouse':
        keyboard.add(KeyboardButton("📦 Ожидающие доставки"))
        keyboard.add(KeyboardButton("✅ Принятые товары"))
    elif user_role == 'admin':
        keyboard.add(KeyboardButton("👥 Управление пользователями"))
        keyboard.add(KeyboardButton("📊 Статистика"))
    
    keyboard.add(KeyboardButton("ℹ️ Помощь"))
    return keyboard

def get_role_keyboard():
    """Клавиатура выбора роли"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("👤 Покупатель"))
    keyboard.add(KeyboardButton("🏪 Продавец"))
    keyboard.add(KeyboardButton("🏭 Человек на складе"))
    return keyboard

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user = db.get_user(message.from_user.id)
    
    if user:
        if user['is_approved']:
            await message.answer(
                f"Добро пожаловать, {user['first_name']}!\n"
                f"Ваша роль: {user['role']}\n"
                f"Время: {get_current_time()}",
                reply_markup=get_main_keyboard(user['role'])
            )
        else:
            await message.answer(
                "Ваша заявка на регистрацию ожидает одобрения администратора. "
                "Вы получите уведомление, когда администратор одобрит вашу заявку."
            )
    else:
        await message.answer(
            "Добро пожаловать в систему SFX Savdo!\n"
            "Для начала работы необходимо зарегистрироваться.\n"
            "Введите ваше полное имя:"
        )
        await state.set_state(RegistrationStates.waiting_for_name)

@router.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext):
    """Обработчик команды /register"""
    user = db.get_user(message.from_user.id)
    
    if user and user['is_approved']:
        await message.answer("Вы уже зарегистрированы и одобрены!")
        return
    
    await message.answer("Введите ваше полное имя:")
    await state.set_state(RegistrationStates.waiting_for_name)

# Обработчики регистрации
@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка ввода телефона"""
    await state.update_data(phone=message.text)
    await message.answer(
        "Выберите вашу роль:",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_role)

@router.message(RegistrationStates.waiting_for_role)
async def process_role(message: types.Message, state: FSMContext):
    """Обработка выбора роли"""
    role_mapping = {
        "👤 Покупатель": "buyer",
        "🏪 Продавец": "seller", 
        "🏭 Человек на складе": "warehouse"
    }
    
    if message.text not in role_mapping:
        await message.answer("Пожалуйста, выберите роль из предложенных вариантов:")
        return
    
    role = role_mapping[message.text]
    user_data = await state.get_data()
    
    # Регистрация пользователя
    user_id = db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=user_data['name'],
        last_name="",
        phone=user_data['phone'],
        role=role
    )
    
    if role == 'seller':
        # Продавцы автоматически одобряются
        db.approve_user(message.from_user.id)
        await message.answer(
            "Регистрация успешно завершена! Вы можете начать работу.",
            reply_markup=get_main_keyboard(role)
        )
    else:
        # Покупатели и люди на складе требуют одобрения админа
        await message.answer(
            "Регистрация завершена! Ваша заявка отправлена администратору на одобрение. "
            "Вы получите уведомление, когда администратор одобрит вашу заявку."
        )
        
        # Уведомление администраторов
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🔔 Новая заявка на регистрацию!\n"
                    f"Имя: {user_data['name']}\n"
                    f"Телефон: {user_data['phone']}\n"
                    f"Роль: {role}\n"
                    f"Telegram ID: {message.from_user.id}"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    await state.clear()

# Административные команды
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Панель администратора"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи ожидающие одобрения", callback_data="admin_pending_users")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="➕ Добавить покупателя", callback_data="admin_add_buyer")],
        [InlineKeyboardButton(text="➕ Добавить человека на складе", callback_data="admin_add_warehouse")]
    ])
    
    await message.answer("Панель администратора:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith('admin_'))
async def process_admin_callback(callback_query: types.CallbackQuery):
    """Обработка административных callback'ов"""
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("У вас нет прав администратора!")
        return
    
    action = callback_query.data
    
    if action == "admin_pending_users":
        # Получение пользователей ожидающих одобрения
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT * FROM users 
            WHERE is_approved = FALSE AND role != 'seller'
            ORDER BY created_at DESC
        """)
        pending_users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not pending_users:
            await callback_query.message.answer("Нет пользователей ожидающих одобрения.")
            return
        
        text = "👥 Пользователи ожидающие одобрения:\n\n"
        for user in pending_users:
            text += f"ID: {user['telegram_id']}\n"
            text += f"Имя: {user['first_name']}\n"
            text += f"Телефон: {user['phone']}\n"
            text += f"Роль: {user['role']}\n"
            text += f"Дата: {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            text += "─" * 30 + "\n"
        
        await callback_query.message.answer(text)
    
    elif action == "admin_add_buyer":
        await callback_query.message.answer(
            "Для добавления покупателя, попросите его отправить команду /register и выбрать роль 'Покупатель'"
        )
    
    elif action == "admin_add_warehouse":
        await callback_query.message.answer(
            "Для добавления человека на складе, попросите его отправить команду /register и выбрать роль 'Человек на складе'"
        )
    
    await callback_query.answer()

# Команда для одобрения пользователей
@router.message(Command("approve"))
async def cmd_approve(message: types.Message):
    """Одобрение пользователя администратором"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора!")
        return
    
    try:
        telegram_id = int(message.text.split()[1])
        db.approve_user(telegram_id)
        
        # Уведомление пользователя
        try:
            await bot.send_message(
                telegram_id,
                "✅ Ваша заявка на регистрацию одобрена! Теперь вы можете использовать бота."
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {telegram_id}: {e}")
        
        await message.answer(f"Пользователь {telegram_id} успешно одобрен!")
        
    except (IndexError, ValueError):
        await message.answer("Использование: /approve <telegram_id>")

# Команда для отклонения пользователей
@router.message(Command("reject"))
async def cmd_reject(message: types.Message):
    """Отклонение пользователя администратором"""
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав администратора!")
        return
    
    try:
        telegram_id = int(message.text.split()[1])
        
        # Удаление пользователя из базы
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE telegram_id = %s", (telegram_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Уведомление пользователя
        try:
            await bot.send_message(
                telegram_id,
                "❌ Ваша заявка на регистрацию отклонена администратором."
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {telegram_id}: {e}")
        
        await message.answer(f"Пользователь {telegram_id} отклонен и удален из системы!")
        
    except (IndexError, ValueError):
        await message.answer("Использование: /reject <telegram_id>")

# Обработчик текстовых сообщений
@router.message()
async def handle_text(message: types.Message):
    """Обработка текстовых сообщений"""
    user = db.get_user(message.from_user.id)
    
    if not user or not user['is_approved']:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /register")
        return
    
    text = message.text
    
    if text == "ℹ️ Помощь":
        await show_help(message, user['role'])
    elif text == "📋 Создать заявку" and user['role'] == 'buyer':
        await start_purchase_request(message)
    elif text == "📊 Мои заявки" and user['role'] == 'buyer':
        await show_my_requests(message)
    elif text == "📋 Активные заявки" and user['role'] == 'seller':
        await show_active_requests(message)
    elif text == "📦 Ожидающие доставки" and user['role'] == 'warehouse':
        await show_pending_deliveries(message)
    else:
        await message.answer("Используйте кнопки меню для навигации.")

async def show_help(message: types.Message, role: str):
    """Показать справку"""
    help_text = "📚 Справка по использованию бота:\n\n"
    
    if role == 'buyer':
        help_text += "👤 Покупатель:\n"
        help_text += "• Создавайте заявки на покупку товаров\n"
        help_text += "• Получайте предложения от продавцов\n"
        help_text += "• Отслеживайте статус заказов\n\n"
    elif role == 'seller':
        help_text += "🏪 Продавец:\n"
        help_text += "• Просматривайте активные заявки\n"
        help_text += "• Отправляйте предложения покупателям\n"
        help_text += "• Отслеживайте свои предложения\n\n"
    elif role == 'warehouse':
        help_text += "🏭 Человек на складе:\n"
        help_text += "• Принимайте товары от продавцов\n"
        help_text += "• Подтверждайте получение товаров\n"
        help_text += "• Уведомляйте покупателей\n\n"
    
    help_text += "⏰ Время: " + get_current_time()
    await message.answer(help_text)

async def start_purchase_request(message: types.Message):
    """Начать создание заявки на покупку"""
    await message.answer("Введите название поставщика:")
    # Здесь нужно добавить FSM для создания заявки

async def show_my_requests(message: types.Message):
    """Показать заявки покупателя"""
    await message.answer("Функция в разработке...")

async def show_active_requests(message: types.Message):
    """Показать активные заявки для продавцов"""
    await message.answer("Функция в разработке...")

async def show_pending_deliveries(message: types.Message):
    """Показать ожидающие доставки для склада"""
    await message.answer("Функция в разработке...")

# Запуск бота
async def main():
    """Главная функция"""
    # Создание таблиц базы данных
    db.create_tables()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 