import asyncio
import logging
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN, ADMIN_IDS, TIMEZONE
from database import Database
from excel_handler import ExcelHandler
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

# Инициализация базы данных и Excel обработчика
db = Database()
excel_handler = ExcelHandler()

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
    waiting_for_excel_file = State()

class SellerOfferStates(StatesGroup):
    waiting_for_price = State()
    waiting_for_total = State()
    waiting_for_excel_offer = State()

class BuyerApprovalStates(StatesGroup):
    waiting_for_offer_approval = State()

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
    if user_role == 'buyer':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Создать заявку")],
                [KeyboardButton(text="📊 Мои заявки")],
                [KeyboardButton(text="📦 Мои заказы")],
                [KeyboardButton(text="ℹ️ Помощь")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'seller':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Активные заявки")],
                [KeyboardButton(text="💼 Мои предложения")],
                [KeyboardButton(text="ℹ️ Помощь")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'warehouse':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Ожидающие доставки")],
                [KeyboardButton(text="✅ Принятые товары")],
                [KeyboardButton(text="ℹ️ Помощь")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'admin':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 Управление пользователями")],
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="ℹ️ Помощь")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="ℹ️ Помощь")]],
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

def get_contact_keyboard():
    """Клавиатура для отправки контакта"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Отправить контакт", request_contact=True)]
        ],
        resize_keyboard=True
    )
    return keyboard

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user = db.get_user(message.from_user.id)
    
    if user:
        if user['is_approved']:
            await message.answer(
                f"Добро пожаловать, {user['full_name']}!\n"
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

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    await state.update_data(name=message.text)
    await message.answer(
        "Введите ваш номер телефона или нажмите кнопку для отправки контакта:",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    """Обработка отправки контакта"""
    contact = message.contact
    phone = contact.phone_number
    if phone.startswith('+'):
        phone = phone[1:]  # Убираем + если есть
    
    await state.update_data(phone=phone)
    await message.answer(
        "Выберите вашу роль:",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_role)

@router.message(RegistrationStates.waiting_for_role)
async def process_role(message: types.Message, state: FSMContext):
    """Обработка выбора роли"""
    role_mapping = {
        "👤 Заказчик": "buyer",
        "🏪 Поставщик": "seller", 
        "🏭 Зав. Склад": "warehouse"
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
        full_name=user_data['name'],
        phone=user_data['phone'],
        role=role
    )
    
    if role == 'seller':
        # Поставщики автоматически одобряются
        db.approve_user(message.from_user.id)
        await message.answer(
            "Регистрация успешно завершена! Вы можете начать работу.",
            reply_markup=get_main_keyboard(role)
        )
    else:
        # Заказчики и зав. склада требуют одобрения админа
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
        [InlineKeyboardButton(text="➕ Добавить заказчика", callback_data="admin_add_buyer")],
        [InlineKeyboardButton(text="➕ Добавить зав. склада", callback_data="admin_add_warehouse")]
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
            text += f"Имя: {user['full_name']}\n"
            text += f"Телефон: {user['phone_number']}\n"
            text += f"Роль: {user['role']}\n"
            text += f"Дата: {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            text += "─" * 30 + "\n"
        
        await callback_query.message.answer(text)
    
    elif action == "admin_add_buyer":
        await callback_query.message.answer(
            "Для добавления заказчика, попросите его отправить команду /register и выбрать роль 'Заказчик'"
        )
    
    elif action == "admin_add_warehouse":
        await callback_query.message.answer(
            "Для добавления зав. склада, попросите его отправить команду /register и выбрать роль 'Зав. Склад'"
        )
    
    await callback_query.answer()

# Обработчики для Excel и предложений
@router.callback_query(lambda c: c.data.startswith('create_'))
async def process_create_request(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка создания заявки"""
    action = callback_query.data
    
    if action == "create_excel_request":
        # Создаем шаблон Excel
        excel_file = excel_handler.create_purchase_request_template()
        await callback_query.message.answer_document(
            types.BufferedInputFile(
                excel_file.getvalue(),
                filename="заявка_шаблон.xlsx"
            ),
            caption="📊 Заполните этот шаблон и отправьте обратно:"
        )
        await state.set_state(PurchaseRequestStates.waiting_for_excel_file)
        
    elif action == "create_text_request":
        await callback_query.message.answer(
            "📝 Введите данные заявки в текстовом формате.\n\n"
            "Формат:\n"
            "Поставщик: [название поставщика]\n"
            "Объект: [название объекта]\n"
            "Товар: [название товара]\n"
            "Количество: [число]\n"
            "Единица: [шт/кг/м и т.д.]\n"
            "Описание: [дополнительная информация]"
        )
        await state.set_state(PurchaseRequestStates.waiting_for_supplier)
    
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('send_offer_'))
async def process_send_offer(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка отправки предложения"""
    request_id = int(callback_query.data.split('_')[2])
    
    # Получаем данные заявки с товарами
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT pr.id, pr.buyer_id, pr.supplier as supplier_name, pr.object_name, pr.status, pr.created_at
        FROM purchase_requests pr
        WHERE pr.id = %s
    """, (request_id,))
    request = cursor.fetchone()
    
    if request:
        # Получаем товары заявки
        cursor.execute("""
            SELECT * FROM request_items 
            WHERE request_id = %s 
            ORDER BY created_at
        """, (request_id,))
        request['items'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not request:
        await callback_query.message.answer("❌ Заявка не найдена.")
        await callback_query.answer()
        return
    
    # Сохраняем ID заявки в состоянии
    await state.update_data(request_id=request_id)
    
    # Создаем шаблон предложения со всеми товарами
    request_data = {
        'supplier_name': request['supplier_name'],
        'object_name': request['object_name'],
        'items': request['items']
    }
    
    excel_file = excel_handler.create_seller_offer_template(request_data)
    await callback_query.message.answer_document(
        types.BufferedInputFile(
            excel_file.getvalue(),
            filename="предложение_шаблон.xlsx"
        ),
        caption="💼 Заполните цены в желтых ячейках и отправьте обратно:"
    )
    await state.set_state(SellerOfferStates.waiting_for_excel_offer)
    await callback_query.answer()

# Обработчики Excel файлов
@router.message(PurchaseRequestStates.waiting_for_excel_file, F.document)
async def process_excel_request(message: types.Message, state: FSMContext):
    """Обработка Excel файла с заявкой"""
    try:
        # Скачиваем файл
        file = await bot.get_file(message.document.file_id)
        file_content = await bot.download_file(file.file_path)
        
        # Проверяем структуру файла
        is_valid, error_msg = excel_handler.validate_excel_structure(file_content.read(), 'request')
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
        
        file_content.seek(0)
        # Парсим Excel
        request_data = excel_handler.parse_purchase_request(file_content.read())
        
        if not request_data['items']:
            await message.answer("❌ Файл пуст или имеет неверный формат.")
            return
        
        # Сохраняем заявку в базе данных
        user = db.get_user(message.from_user.id)
        
        request_id = db.add_purchase_request(
            buyer_id=user['id'],
            supplier_name=request_data['supplier_name'],
            object_name=request_data['object_name']
        )
        
        # Сохраняем товары заявки
        for item in request_data['items']:
            db.add_request_item(
                request_id=request_id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit=item['unit'],
                material_description=item['material_description']
            )
        
        # Отправляем всем поставщикам
        sellers = db.get_users_by_role('seller')
        for seller in sellers:
            try:
                # Создаем сообщение с информацией о заявке
                message_text = f"📋 Новая заявка на покупку!\n\n"
                message_text += f"🏢 Поставщик: {request_data['supplier_name']}\n"
                message_text += f"🏗️ Объект: {request_data['object_name']}\n"
                message_text += f"📦 Количество товаров: {len(request_data['items'])}\n\n"
                
                # Добавляем информацию о товарах
                for i, item in enumerate(request_data['items'][:3], 1):  # Показываем первые 3 товара
                    message_text += f"{i}. {item['product_name']} - {item['quantity']} {item['unit']}\n"
                
                if len(request_data['items']) > 3:
                    message_text += f"... и еще {len(request_data['items']) - 3} товаров\n"
                
                await bot.send_message(
                    seller['telegram_id'],
                    message_text
                )
            except Exception as e:
                logger.error(f"Failed to send request to seller {seller['telegram_id']}: {e}")
        
        await message.answer(
            f"✅ Заявка с {len(request_data['items'])} товарами успешно создана и отправлена {len(sellers)} поставщикам!",
            reply_markup=get_main_keyboard(user['role'])
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")

@router.message(SellerOfferStates.waiting_for_excel_offer, F.document)
async def process_excel_offer(message: types.Message, state: FSMContext):
    """Обработка Excel файла с предложением поставщика"""
    try:
        # Скачиваем файл
        file = await bot.get_file(message.document.file_id)
        file_content = await bot.download_file(file.file_path)
        
        # Проверяем структуру файла
        is_valid, error_msg = excel_handler.validate_excel_structure(file_content.read(), 'offer')
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
        
        file_content.seek(0)
        # Парсим Excel
        offer_data = excel_handler.parse_seller_offer(file_content.read())
        
        if not offer_data['items']:
            await message.answer("❌ Файл пуст или не содержит предложений с ценами.")
            return
        
        # Получаем данные из состояния
        state_data = await state.get_data()
        request_id = state_data.get('request_id')
        
        if not request_id:
            await message.answer("❌ Ошибка: не найдена заявка.")
            return
        
        # Сохраняем предложение в базе данных
        user = db.get_user(message.from_user.id)
        
        offer_id = db.add_seller_offer(
            request_id=request_id,
            seller_id=user['id'],
            total_amount=offer_data['total_amount']
        )
        
        # Сохраняем товары предложения
        for item in offer_data['items']:
            db.add_offer_item(
                offer_id=offer_id,
                product_name=item['product_name'],
                quantity=item['quantity'],
                unit=item['unit'],
                price_per_unit=item['price_per_unit'],
                total_price=item['total_price'],
                material_description=item['material_description']
            )
        
        # Уведомляем заказчика
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT pr.id, pr.buyer_id, 
                   COALESCE(pr.supplier, 'Не указан') as supplier_name, 
                   COALESCE(pr.object_name, 'Не указан') as object_name,
                   pr.status, pr.created_at,
                   u.telegram_id as buyer_telegram_id, u.full_name as buyer_name
            FROM purchase_requests pr
            JOIN users u ON pr.buyer_id = u.id
            WHERE pr.id = %s
        """, (request_id,))
        request = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if request:
            try:
                # Получаем все предложения для этой заявки
                offers = db.get_offers_for_request(request_id)
                
                # Создаем сводку предложений
                summary = excel_handler.create_offers_summary(offers, request['buyer_name'])
                
                # Создаем Excel файл с предложениями
                excel_file = excel_handler.create_offers_excel(offers, request['buyer_name'])
                
                # Создаем кнопки для каждого предложения
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                for offer in offers:
                    keyboard.inline_keyboard.append([
                        InlineKeyboardButton(
                            text=f"✅ Одобрить #{offer['id']}", 
                            callback_data=f"approve_offer_{offer['id']}"
                        ),
                        InlineKeyboardButton(
                            text=f"❌ Отклонить #{offer['id']}", 
                            callback_data=f"reject_offer_{offer['id']}"
                        )
                    ])
                
                # Отправляем Excel файл покупателю
                await bot.send_document(
                    request['buyer_telegram_id'],
                    types.BufferedInputFile(
                        excel_file.getvalue(),
                        filename=f"предложения_заявка_{request_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    ),
                    caption="📊 Excel файл с предложениями поставщиков"
                )
                
                # Отправляем сводку покупателю с кнопками
                await bot.send_message(
                    request['buyer_telegram_id'],
                    summary,
                    reply_markup=keyboard
                )
                
                await message.answer(
                    f"✅ Предложение успешно отправлено заказчику!",
                    reply_markup=get_main_keyboard(user['role'])
                )
                
            except Exception as e:
                logger.error(f"Failed to notify buyer {request['buyer_telegram_id']}: {e}")
                await message.answer("✅ Предложение сохранено, но не удалось уведомить заказчика.")
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")

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

# Обработчики для одобрения предложений
@router.callback_query(lambda c: c.data.startswith('approve_offer_'))
async def process_approve_offer(callback_query: types.CallbackQuery):
    """Одобрение предложения заказчиком"""
    try:
        offer_id = int(callback_query.data.split('_')[2])
        user = db.get_user(callback_query.from_user.id)
        
        if not user or user['role'] != 'buyer':
            await callback_query.answer("❌ Только заказчики могут одобрять предложения!")
            return
        
        # Получаем данные предложения
        offer = db.get_offer_with_items(offer_id)
        if not offer:
            await callback_query.answer("❌ Предложение не найдено!")
            return
        
        # Обновляем статус предложения
        db.update_offer_status(offer_id, 'approved')
        
        # Уведомляем поставщика
        try:
            await bot.send_message(
                offer['seller_telegram_id'],
                f"✅ Ваше предложение #{offer_id} одобрено заказчиком!\n"
                f"💵 Общая сумма: {offer['total_amount']:,} сум\n"
                f"📅 Дата одобрения: {get_current_time()}"
            )
        except Exception as e:
            logger.error(f"Failed to notify seller {offer['seller_telegram_id']}: {e}")
        
        await callback_query.message.edit_text(
            f"✅ Предложение #{offer_id} одобрено!\n"
            f"👤 Поставщик: {offer['full_name']}\n"
            f"💵 Сумма: {offer['total_amount']:,} сум"
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith('reject_offer_'))
async def process_reject_offer(callback_query: types.CallbackQuery):
    """Отклонение предложения заказчиком"""
    try:
        offer_id = int(callback_query.data.split('_')[2])
        user = db.get_user(callback_query.from_user.id)
        
        if not user or user['role'] != 'buyer':
            await callback_query.answer("❌ Только заказчики могут отклонять предложения!")
            return
        
        # Получаем данные предложения
        offer = db.get_offer_with_items(offer_id)
        if not offer:
            await callback_query.answer("❌ Предложение не найдено!")
            return
        
        # Обновляем статус предложения
        db.update_offer_status(offer_id, 'rejected')
        
        # Уведомляем поставщика
        try:
            await bot.send_message(
                offer['seller_telegram_id'],
                f"❌ Ваше предложение #{offer_id} отклонено заказчиком.\n"
                f"📅 Дата отклонения: {get_current_time()}"
            )
        except Exception as e:
            logger.error(f"Failed to notify seller {offer['seller_telegram_id']}: {e}")
        
        await callback_query.message.edit_text(
            f"❌ Предложение #{offer_id} отклонено.\n"
            f"👤 Поставщик: {offer['full_name']}"
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

# Обработчик текстовых сообщений
@router.message()
async def handle_text(message: types.Message, state: FSMContext):
    """Обработка текстовых сообщений"""
    user = db.get_user(message.from_user.id)
    
    if not user or not user['is_approved']:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь с помощью /register")
        return
    
    text = message.text
    
    if text == "ℹ️ Помощь":
        await show_help(message, user['role'])
    elif text == "📋 Создать заявку" and user['role'] == 'buyer':
        await start_purchase_request(message, state)
    elif text == "📊 Мои заявки" and user['role'] == 'buyer':
        await show_my_requests(message)
    elif text == "📦 Мои заказы" and user['role'] == 'buyer':
        await show_my_orders(message)
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
        help_text += "👤 Заказчик:\n"
        help_text += "• Создавайте заявки на покупку товаров\n"
        help_text += "• Получайте предложения от поставщиков\n"
        help_text += "• Отслеживайте статус заказов\n\n"
    elif role == 'seller':
        help_text += "🏪 Поставщик:\n"
        help_text += "• Просматривайте активные заявки\n"
        help_text += "• Отправляйте предложения заказчикам\n"
        help_text += "• Отслеживайте свои предложения\n\n"
    elif role == 'warehouse':
        help_text += "🏭 Зав. Склад:\n"
        help_text += "• Принимайте товары от поставщиков\n"
        help_text += "• Подтверждайте получение товаров\n"
        help_text += "• Уведомляйте заказчиков\n\n"
    
    help_text += "⏰ Время: " + get_current_time()
    await message.answer(help_text)

async def start_purchase_request(message: types.Message, state: FSMContext):
    """Начать создание заявки на покупку"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Excel файл", callback_data="create_excel_request")],
        [InlineKeyboardButton(text="📝 Текстовый формат", callback_data="create_text_request")]
    ])
    
    await message.answer(
        "📋 Создание заявки на покупку\n\n"
        "Выберите формат заявки:",
        reply_markup=keyboard
    )

async def show_my_requests(message: types.Message):
    """Показать заявки заказчика"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'buyer':
        await message.answer("❌ Только заказчики могут просматривать заявки.")
        return
    
    # Получаем заявки пользователя
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id, buyer_id, 
               COALESCE(supplier, 'Не указан') as supplier_name, 
               COALESCE(object_name, 'Не указан') as object_name,
               status, created_at
        FROM purchase_requests 
        WHERE buyer_id = %s 
        ORDER BY created_at DESC
    """, (user['id'],))
    requests = cursor.fetchall()
    
    # Получаем товары для каждой заявки
    for request in requests:
        cursor.execute("""
            SELECT * FROM request_items 
            WHERE request_id = %s 
            ORDER BY created_at
        """, (request['id'],))
        request['items'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not requests:
        await message.answer("📭 У вас пока нет заявок.")
        return
    
    for req in requests[:5]:  # Показываем последние 5 заявок
        text = f"📋 **Заявка #{req['id']}**\n\n"
        text += f"🏢 Поставщик: {req['supplier_name']}\n"
        text += f"🏗️ Объект: {req['object_name']}\n"
        text += f"📦 Количество товаров: {len(req['items'])}\n"
        text += f"📅 Дата: {req['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        text += f"📊 Статус: {req['status']}\n\n"
        
        # Добавляем информацию о товарах
        text += "📋 **Товары:**\n"
        if req['items']:
            for i, item in enumerate(req['items'][:3], 1):  # Показываем первые 3 товара
                text += f"{i}. {item['product_name']} - {item['quantity']} {item['unit']}\n"
                if item['material_description']:
                    text += f"   📝 {item['material_description']}\n"
            
            if len(req['items']) > 3:
                text += f"... и еще {len(req['items']) - 3} товаров\n"
        else:
            text += "Товары не загружены\n"
        
        await message.answer(text)

async def show_active_requests(message: types.Message):
    """Показать активные заявки для поставщиков"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'seller':
        await message.answer("❌ Только поставщики могут просматривать активные заявки.")
        return
    
    # Получаем активные заявки
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT pr.id, pr.buyer_id, 
               COALESCE(pr.supplier, 'Не указан') as supplier_name, 
               COALESCE(pr.object_name, 'Не указан') as object_name,
               pr.status, pr.created_at,
               u.full_name as buyer_name 
        FROM purchase_requests pr
        JOIN users u ON pr.buyer_id = u.id
        WHERE pr.status = 'active'
        ORDER BY pr.created_at DESC
    """)
    requests = cursor.fetchall()
    
    # Получаем товары для каждой заявки
    for request in requests:
        cursor.execute("""
            SELECT * FROM request_items 
            WHERE request_id = %s 
            ORDER BY created_at
        """, (request['id'],))
        request['items'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not requests:
        await message.answer("📭 Нет активных заявок.")
        return
    
    # Создаем Excel файл с активными заявками
    excel_file = excel_handler.create_active_requests_excel(requests, user['full_name'])
    
    # Отправляем Excel файл
    await message.answer_document(
        types.BufferedInputFile(
            excel_file.getvalue(),
            filename=f"активные_заявки_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        ),
        caption="📋 Excel файл с активными заявками"
    )
    
    for req in requests[:5]:  # Показываем последние 5 заявок
        text = f"📋 **Заявка #{req['id']}**\n\n"
        text += f"👤 Заказчик: {req['buyer_name']}\n"
        text += f"🏢 Поставщик: {req['supplier_name']}\n"
        text += f"🏗️ Объект: {req['object_name']}\n"
        text += f"📦 Количество товаров: {len(req['items'])}\n"
        text += f"📅 Дата: {req['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Добавляем информацию о товарах
        text += "📋 **Товары:**\n"
        if req['items']:
            for i, item in enumerate(req['items'][:3], 1):  # Показываем первые 3 товара
                text += f"{i}. {item['product_name']} - {item['quantity']} {item['unit']}\n"
                if item['material_description']:
                    text += f"   📝 {item['material_description']}\n"
            
            if len(req['items']) > 3:
                text += f"... и еще {len(req['items']) - 3} товаров\n"
        else:
            text += "Товары не загружены\n"
        
        # Кнопка для отправки предложения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💼 Отправить предложение", callback_data=f"send_offer_{req['id']}")]
        ])
        
        await message.answer(text, reply_markup=keyboard)

async def show_my_orders(message: types.Message):
    """Показать одобренные заказы заказчика"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'buyer':
        await message.answer("❌ Только заказчики могут просматривать заказы.")
        return
    
    # Получаем одобренные предложения
    approved_offers = db.get_approved_offers_for_buyer(user['id'])
    
    if not approved_offers:
        await message.answer("📭 У вас пока нет одобренных заказов.")
        return
    
    # Создаем Excel файл с одобренными заказами
    excel_file = excel_handler.create_offers_excel(approved_offers, user['full_name'])
    
    # Отправляем Excel файл
    await message.answer_document(
        types.BufferedInputFile(
            excel_file.getvalue(),
            filename=f"одобренные_заказы_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        ),
        caption="📦 Excel файл с одобренными заказами"
    )
    
    # Отправляем текстовую сводку
    for offer in approved_offers[:5]:  # Показываем последние 5 заказов
        text = f"📦 **Заказ #{offer['id']}**\n\n"
        text += f"🏢 Поставщик: {offer['supplier_name']}\n"
        text += f"🏗️ Объект: {offer['object_name']}\n"
        text += f"👤 Поставщик: {offer['full_name']}\n"
        text += f"📞 Телефон: {offer['phone_number']}\n"
        text += f"💵 Общая сумма: {offer['total_amount']:,} сум\n"
        text += f"📅 Дата: {offer['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Детали товаров
        text += "📋 **Товары:**\n"
        for i, item in enumerate(offer['items'], 1):
            text += f"{i}. {item['product_name']}\n"
            text += f"   📊 Количество: {item['quantity']} {item['unit']}\n"
            text += f"   💰 Цена за единицу: {item['price_per_unit']:,} сум\n"
            text += f"   💵 Сумма: {item['total_price']:,} сум\n"
            if item['material_description']:
                text += f"   📝 Описание: {item['material_description']}\n"
            text += "\n"
        
        await message.answer(text)

async def show_pending_deliveries(message: types.Message):
    """Показать ожидающие доставки для склада"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        await message.answer("❌ Только люди на складе могут просматривать доставки.")
        return
    
    await message.answer("📦 Функция просмотра доставок в разработке...")

# Запуск бота
async def main():
    """Главная функция"""
    # Создание таблиц базы данных
    db.create_tables()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 