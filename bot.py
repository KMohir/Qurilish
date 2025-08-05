import asyncio
import logging
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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

class SellerDeliveryStates(StatesGroup):
    waiting_for_shipment_confirmation = State()

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
                [KeyboardButton(text="📋 Ариза яратиш")],
                [KeyboardButton(text="📊 Менинг аризаларим")],
                [KeyboardButton(text="📦 Менинг буюртмаларим")],
                [KeyboardButton(text="ℹ️ Ёрдам")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'seller':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📋 Фаол аризалар")],
                [KeyboardButton(text="💼 Менинг таклифларим")],
                [KeyboardButton(text="ℹ️ Ёрдам")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'warehouse':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📦 Кутган етказиб беришлар")],
                [KeyboardButton(text="✅ Кабул қилинган товарлар")],
                [KeyboardButton(text="ℹ️ Ёрдам")]
            ],
            resize_keyboard=True
        )
    elif user_role == 'admin':
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 Фойдаланувчиларни бошқариш")],
                [KeyboardButton(text="📊 Статистика")],
                [KeyboardButton(text="ℹ️ Ёрдам")]
            ],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="ℹ️ Ёрдам")]],
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
            [KeyboardButton(text="📞 Менинг рақамини юбориш", request_contact=True)]
        ],
        resize_keyboard=True
    )
    return keyboard

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    # Очищаем состояние при старте
    await state.clear()
    print(f"DEBUG: Состояние очищено для пользователя {message.from_user.id}")
    
    user = db.get_user(message.from_user.id)
    
    if user:
        if user['is_approved']:
            await message.answer(
                f"Хуш келибсиз, {user['full_name']}!\n"
                f"Ролингиз: {user['role']}\n"
                f"Вақт: {get_current_time()}",
                reply_markup=get_main_keyboard(user['role'])
            )
            print(f"DEBUG: Показано главное меню для пользователя {message.from_user.id} с ролью {user['role']}")
        else:
            await message.answer(
                "Рўйхатдан ўтиш аризангиз маъмур тасдиқлашини кутмоқда. "
                "Маъмур аризангизни тасдиқлаганда хабар оласиз."
            )
    else:
        await message.answer(
            "SFX Savdo тизимига хуш келибсиз! 📋\n\n"
            "Рўйхатдан ўтиш учун бизга керак:\n"
            "1️⃣ Тўлиқ исмингиз\n"
            "2️⃣ Telegram-га богланган рақамингиз\n"
            "3️⃣ Тизимдаги ролингиз\n\n"
            "Исмдан бошлаймиз. Тўлиқ исмингизни киритинг:"
        )
        await state.set_state(RegistrationStates.waiting_for_name)

@router.message(Command("register"))
async def cmd_register(message: types.Message, state: FSMContext):
    """Обработчик команды /register"""
    user = db.get_user(message.from_user.id)
    
    if user and user['is_approved']:
        await message.answer("Сиз аллақачон рўйхатдан ўтган ва тасдиқлангансиз!")
        return
    
    await message.answer(
        "SFX Savdo тизимига хуш келибсиз! 📋\n\n"
        "Рўйхатдан ўтиш учун бизга керак:\n"
        "1️⃣ Тўлиқ исмингиз\n"
        "2️⃣ Telegram-га богланган рақамингиз\n"
        "3️⃣ Тизимдаги ролингиз\n\n"
        "Исмдан бошлаймиз. Тўлиқ исмингизни киритинг:"
    )
    await state.set_state(RegistrationStates.waiting_for_name)

# Обработчики регистрации
@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    await state.update_data(name=message.text)
    await message.answer(
        "Рақамингизни юбориш учун тўғридаги тугмани босинг:",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_phone)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_contact(message: types.Message, state: FSMContext):
    """Обработка отправки контакта"""
    print("DEBUG: === ОБРАБОТЧИК КОНТАКТА СРАБОТАЛ ===")
    contact = message.contact
    
    # Добавляем отладочную информацию
    print(f"DEBUG: Получен контакт от пользователя {message.from_user.id}")
    print(f"DEBUG: contact.phone_number = {contact.phone_number}")
    print(f"DEBUG: contact.user_id = {contact.user_id}")
    print(f"DEBUG: message.from_user.id = {message.from_user.id}")
    print(f"DEBUG: contact.first_name = {contact.first_name}")
    print(f"DEBUG: contact.last_name = {contact.last_name}")
    
    # Упрощаем логику - принимаем любой контакт
    phone = contact.phone_number
    if phone.startswith('+'):
        phone = phone[1:]  # Убираем + если есть
    
    await state.update_data(phone=phone)
    await message.answer(
        f"✅ Телефон рақами олинди: {contact.phone_number}\n\n"
        "Энди ролингизни танланг:",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_role)
    print("DEBUG: === ОБРАБОТЧИК КОНТАКТА ЗАВЕРШЕН ===")

@router.message(RegistrationStates.waiting_for_phone)
async def process_phone_input(message: types.Message, state: FSMContext):
    """Обработка ввода телефона - только контакт"""
    print(f"DEBUG: Получено сообщение в состоянии ожидания телефона")
    print(f"DEBUG: Тип сообщения: {message.content_type}")
    print(f"DEBUG: Текст сообщения: {message.text}")
    print(f"DEBUG: Есть ли контакт: {hasattr(message, 'contact')}")
    
    await message.answer(
        "❌ Илтимос, рақамингизни юбориш учун '📞 Менинг рақамини юбориш' тугмасини босинг:",
        reply_markup=get_contact_keyboard()
    )

@router.message(RegistrationStates.waiting_for_role)
async def process_role(message: types.Message, state: FSMContext):
    """Обработка выбора роли"""
    role_mapping = {
        "👤 Заказчик": "buyer",
        "🏪 Поставщик": "seller", 
        "🏭 Зав. Склад": "warehouse"
    }
    
    if message.text not in role_mapping:
        await message.answer("Илтимос, таклиф этилган вариантлардан бирини танланг:")
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
            f"Рўйхатдан ўтиш муваффақиятли якунланди!\n\n"
            f"Хуш келибсиз, {user_data['name']}!\n"
            f"Ролингиз: {role}\n"
            f"Вақт: {get_current_time()}",
            reply_markup=get_main_keyboard(role)
        )
        print(f"DEBUG: Показано главное меню для поставщика {message.from_user.id}")
    else:
        # Заказчики и зав. склада требуют одобрения админа
        await message.answer(
            "Рўйхатдан ўтиш якунланди! Аризангиз маъмурга юборилди тасдиқлаш учун. "
            "Маъмур аризангизни тасдиқлаганда хабар оласиз.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Уведомление администраторов
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🔔 Рўйхатдан ўтиш учун янги ариза!\n"
                    f"Исм: {user_data['name']}\n"
                    f"Телефон: {user_data['phone']}\n"
                    f"Роль: {role}\n"
                    f"Telegram ID: {message.from_user.id}"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    # Принудительно очищаем состояние
    await state.clear()
    print(f"DEBUG: Состояние очищено для пользователя {message.from_user.id}")

# Административные команды
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    """Панель администратора"""
    if not is_admin(message.from_user.id):
        await message.answer("Сизда маъмур ҳуқуқлари йўқ!")
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
        await callback_query.answer("Сизда маъмур ҳуқуқлари йўқ!")
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
            await callback_query.message.answer("Тасдиқлашни кутган фойдаланувчилар йўқ.")
            return
        
        text = "👥 Тасдиқлашни кутган фойдаланувчилар:\n\n"
        for user in pending_users:
            text += f"ID: {user['telegram_id']}\n"
            text += f"Исм: {user['full_name']}\n"
            text += f"Телефон: {user['phone_number']}\n"
            text += f"Роль: {user['role']}\n"
            text += f"Сана: {user['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            text += "─" * 30 + "\n"
        
        await callback_query.message.answer(text)
    
    elif action == "admin_add_buyer":
        await callback_query.message.answer(
            "Заказчик қўшиш учун, унингга /register буйруғини юбориш ва 'Заказчик' ролини танлашни сўранг"
        )
    
    elif action == "admin_add_warehouse":
        await callback_query.message.answer(
            "Зав. склад қўшиш учун, унингга /register буйруғини юбориш ва 'Зав. Склад' ролини танлашни сўранг"
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
            caption="📊 Бу шаблонни тўлдиринг ва қайта юборинг:\n\n"
                   "⚠️ **МУҲИМ:** Бирінчи қаторда поставщик ва объект номини тўлдиринг!\n"
                   "📝 Мисолларда кўрсатилган форматда ёзинг."
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
            await message.answer("❌ Файл бўш ёки нотўғри форматда.")
            return
        
        # Проверяем, что указаны поставщик и объект
        if request_data['supplier_name'] == 'Не указан' or request_data['object_name'] == 'Не указан':
            await message.answer(
                "❌ Илтимос, Excel файлда поставщик ва объект номини тўлдиринг!\n\n"
                "📝 Бирінчи қаторда:\n"
                "• Потсавшик: [поставщик номи]\n"
                "• Обект номи: [объект номи]\n\n"
                "Мисол:\n"
                "• Потсавшик: ООО \"Строитель\"\n"
                "• Обект номи: Жилой комплекс \"Сам Сити\""
            )
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
            f"✅ {len(request_data['items'])} товар билан ариза муваффақиятли яратилди ва {len(sellers)} поставщикка юборилди!",
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
            await message.answer("❌ Файл бўш ёки нархлар билан таклифларни ўз ичига олмаган.")
            return
        
        # Получаем данные из состояния
        state_data = await state.get_data()
        request_id = state_data.get('request_id')
        
        if not request_id:
            await message.answer("❌ Хатолик: ариза топилмади.")
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
                    caption="📊 Поставщиклар таклифлари билан Excel файл"
                )
                
                # Отправляем сводку покупателю с кнопками
                await bot.send_message(
                    request['buyer_telegram_id'],
                    summary,
                    reply_markup=keyboard
                )
                
                await message.answer(
                    f"✅ Таклиф муваффақиятли заказчикка юборилди!",
                    reply_markup=get_main_keyboard(user['role'])
                )
                
            except Exception as e:
                logger.error(f"Failed to notify buyer {request['buyer_telegram_id']}: {e}")
                await message.answer("✅ Таклиф сақланди, лекин заказчикни хабардор қилиш мумкин эмас.")
        
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
        
        # Получаем данные пользователя для показа правильного меню
        user = db.get_user(telegram_id)
        
        # Уведомление пользователя с главным меню
        try:
            if user and user['is_approved']:
                await bot.send_message(
                    telegram_id,
                    f"✅ Ваша заявка на регистрацию одобрена!\n\n"
                    f"Хуш келибсиз, {user['full_name']}!\n"
                    f"Ролингиз: {user['role']}\n"
                    f"Вақт: {get_current_time()}",
                    reply_markup=get_main_keyboard(user['role'])
                )
                print(f"DEBUG: Показано главное меню для одобренного пользователя {telegram_id} с ролью {user['role']}")
            else:
                await bot.send_message(
                    telegram_id,
                    "✅ Ваша заявка на регистрацию одобрена! Теперь вы можете использовать бота."
                )
        except Exception as e:
            logger.error(f"Не удалось уведомить пользователя {telegram_id}: {e}")
        
        await message.answer(f"Фойдаланувчи {telegram_id} муваффақиятли тасдиқланди!")
        
        # Очищаем состояние FSM для одобренного пользователя
        try:
            # Создаем временный диспетчер для очистки состояния
            temp_storage = MemoryStorage()
            temp_dp = Dispatcher(storage=temp_storage)
            temp_state = FSMContext(storage=temp_storage, key=Bot(id=0, token=""), chat=telegram_id, user=telegram_id)
            await temp_state.clear()
            print(f"DEBUG: Состояние очищено для одобренного пользователя {telegram_id}")
        except Exception as e:
            print(f"DEBUG: Не удалось очистить состояние для пользователя {telegram_id}: {e}")
        
    except (IndexError, ValueError):
        await message.answer("Ишлатиш: /approve <telegram_id>")

# Команда для отклонения пользователей
@router.message(Command("clear"))
async def cmd_clear(message: types.Message, state: FSMContext):
    """Очистить состояние FSM"""
    await state.clear()
    await message.answer("✅ Состояние очищено!")

@router.message(Command("reset"))
async def cmd_reset(message: types.Message, state: FSMContext):
    """Сбросить состояние и показать главное меню"""
    await state.clear()
    user = db.get_user(message.from_user.id)
    
    if user and user['is_approved']:
        await message.answer(
            f"🔄 Состояние сброшено!\n"
            f"Хуш келибсиз, {user['full_name']}!\n"
            f"Ролингиз: {user['role']}",
            reply_markup=get_main_keyboard(user['role'])
        )
    else:
        await message.answer("Состояние сброшено. Используйте /register для регистрации.")

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
        
        await message.answer(f"Фойдаланувчи {telegram_id} рад этилди ва тизимдан ўчирилди!")
        
    except (IndexError, ValueError):
        await message.answer("Ишлатиш: /reject <telegram_id>")

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
        
        # Создаем запись доставки
        delivery_id = db.add_delivery(offer_id, None)  # warehouse_user_id будет установлен позже
        
        # Уведомляем поставщика с кнопкой подтверждения отправки
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚚 Товарларни юборилди", callback_data=f"ship_sent_{delivery_id}")]
            ])
            
            await bot.send_message(
                offer['seller_telegram_id'],
                f"✅ Сизнинг таклифингиз #{offer_id} заказчик томонидан тасдиқланди!\n\n"
                f"💵 Умумий сумма: {offer['total_amount']:,} сўм\n"
                f"📅 Тасдиқлаш санаси: {get_current_time()}\n"
                f"📦 Доставка #{delivery_id} яратилди\n\n"
                f"🚚 Илтимос, товарларни складга юборинг ва тўғридаги тугмани босинг:",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Failed to notify seller {offer['seller_telegram_id']}: {e}")
        
        await callback_query.message.edit_text(
            f"✅ Таклиф #{offer_id} тасдиқланди!\n"
            f"👤 Поставщик: {offer['full_name']}\n"
            f"💵 Сумма: {offer['total_amount']:,} сўм\n"
            f"📦 Доставка #{delivery_id} яратилди"
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
                f"❌ Сизнинг таклифингиз #{offer_id} заказчик томонидан рад этилди.\n"
                f"📅 Рад этиш санаси: {get_current_time()}"
            )
        except Exception as e:
            logger.error(f"Failed to notify seller {offer['seller_telegram_id']}: {e}")
        
        await callback_query.message.edit_text(
            f"❌ Таклиф #{offer_id} рад этилди.\n"
            f"👤 Поставщик: {offer['full_name']}"
        )
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

# Обработчики доставки
@router.callback_query(lambda c: c.data.startswith('deliver_'))
async def process_delivery_confirmation(callback_query: types.CallbackQuery):
    """Подтверждение доставки"""
    try:
        delivery_id = int(callback_query.data.split('_')[1])
        user = db.get_user(callback_query.from_user.id)
        
        if not user or user['role'] != 'warehouse':
            await callback_query.answer("❌ Только складские работники могут подтверждать доставки!")
            return
        
        # Получаем данные доставки для уведомления заказчика
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT d.*, so.total_amount, pr.supplier, pr.object_name,
                   u_seller.full_name as seller_name, u_buyer.full_name as buyer_name,
                   u_buyer.telegram_id as buyer_telegram_id
            FROM deliveries d
            JOIN seller_offers so ON d.offer_id = so.id
            JOIN purchase_requests pr ON so.purchase_request_id = pr.id
            JOIN users u_seller ON so.seller_id = u_seller.id
            JOIN users u_buyer ON pr.buyer_id = u_buyer.id
            WHERE d.id = %s
        """, (delivery_id,))
        delivery = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not delivery:
            await callback_query.answer("❌ Доставка не найдена!")
            return
        
        # Обновляем статус доставки
        db.update_delivery_status(delivery_id, 'delivered')
        
        # Уведомляем заказчика
        try:
            await bot.send_message(
                delivery['buyer_telegram_id'],
                f"🎉 **Товарлар келди!**\n\n"
                f"📦 Доставка #{delivery_id}\n"
                f"🏢 Поставщик: {delivery['supplier']}\n"
                f"🏗️ Объект: {delivery['object_name']}\n"
                f"👤 Поставщик: {delivery['seller_name']}\n"
                f"💵 Сумма: {delivery['total_amount']:,} сум\n"
                f"📅 Время получения: {get_current_time()}\n\n"
                f"✅ Товарлар складда тайёр. Олишингиз мумкин!"
            )
        except Exception as e:
            logger.error(f"Failed to notify buyer {delivery['buyer_telegram_id']}: {e}")
        
        await callback_query.message.edit_text(
            f"✅ Доставка #{delivery_id} подтверждена!\n"
            f"📅 Время: {get_current_time()}\n\n"
            f"✅ Заказчик уведомлен о прибытии товаров!"
        )
        await callback_query.answer("✅ Доставка подтверждена!")
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith('goods_received_'))
async def process_goods_received(callback_query: types.CallbackQuery):
    """Склад подтверждает получение товаров"""
    try:
        delivery_id = int(callback_query.data.split('_')[2])
        user = db.get_user(callback_query.from_user.id)
        
        if not user or user['role'] != 'warehouse':
            await callback_query.answer("❌ Только складские работники могут подтверждать получение!")
            return
        
        # Получаем данные доставки
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT d.*, so.total_amount, pr.supplier, pr.object_name,
                   u_seller.full_name as seller_name, u_buyer.full_name as buyer_name,
                   u_buyer.telegram_id as buyer_telegram_id
            FROM deliveries d
            JOIN seller_offers so ON d.offer_id = so.id
            JOIN purchase_requests pr ON so.purchase_request_id = pr.id
            JOIN users u_seller ON so.seller_id = u_seller.id
            JOIN users u_buyer ON pr.buyer_id = u_buyer.id
            WHERE d.id = %s
        """, (delivery_id,))
        delivery = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not delivery:
            await callback_query.answer("❌ Доставка не найдена!")
            return
        
        # Обновляем статус доставки
        db.update_delivery_status(delivery_id, 'received')
        
        # Уведомляем заказчика
        try:
            await bot.send_message(
                delivery['buyer_telegram_id'],
                f"🎉 **Товарлар келди!**\n\n"
                f"📦 Доставка #{delivery_id}\n"
                f"🏢 Поставщик: {delivery['supplier']}\n"
                f"🏗️ Объект: {delivery['object_name']}\n"
                f"👤 Поставщик: {delivery['seller_name']}\n"
                f"💵 Сумма: {delivery['total_amount']:,} сум\n"
                f"📅 Время получения: {get_current_time()}\n\n"
                f"✅ Товарлар складда тайёр. Олишингиз мумкин!"
            )
        except Exception as e:
            logger.error(f"Failed to notify buyer {delivery['buyer_telegram_id']}: {e}")
        
        # Обновляем сообщение склада
        await callback_query.message.edit_text(
            f"✅ **Товарлар қабул қилинди!**\n\n"
            f"📦 Доставка #{delivery_id}\n"
            f"📅 Время получения: {get_current_time()}\n\n"
            f"✅ Заказчик уведомлен о прибытии товаров!"
        )
        await callback_query.answer("✅ Товары получены!")
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith('contact_seller_'))
async def process_contact_seller(callback_query: types.CallbackQuery):
    """Связаться с поставщиком"""
    try:
        phone = callback_query.data.split('_')[2]
        await callback_query.answer(f"📞 Телефон поставщика: {phone}")
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith('contact_buyer_'))
async def process_contact_buyer(callback_query: types.CallbackQuery):
    """Связаться с заказчиком"""
    try:
        phone = callback_query.data.split('_')[2]
        await callback_query.answer(f"📞 Телефон заказчика: {phone}")
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

@router.callback_query(lambda c: c.data.startswith('ship_sent_'))
async def process_shipment_sent(callback_query: types.CallbackQuery):
    """Поставщик подтверждает отправку товаров"""
    try:
        delivery_id = int(callback_query.data.split('_')[2])
        user = db.get_user(callback_query.from_user.id)
        
        if not user or user['role'] != 'seller':
            await callback_query.answer("❌ Только поставщики могут подтверждать отправку!")
            return
        
        # Получаем данные доставки
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT d.*, so.total_amount, pr.supplier, pr.object_name,
                   u_seller.full_name as seller_name, u_buyer.full_name as buyer_name
            FROM deliveries d
            JOIN seller_offers so ON d.offer_id = so.id
            JOIN purchase_requests pr ON so.purchase_request_id = pr.id
            JOIN users u_seller ON so.seller_id = u_seller.id
            JOIN users u_buyer ON pr.buyer_id = u_buyer.id
            WHERE d.id = %s
        """, (delivery_id,))
        delivery = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not delivery:
            await callback_query.answer("❌ Доставка не найдена!")
            return
        
        # Уведомляем всех складских работников
        warehouse_users = db.get_users_by_role('warehouse')
        for warehouse_user in warehouse_users:
            try:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Товарлар келди", callback_data=f"goods_received_{delivery_id}")]
                ])
                
                await bot.send_message(
                    warehouse_user['telegram_id'],
                    f"📦 **Товарлар складга келди!**\n\n"
                    f"📦 Доставка #{delivery_id}\n"
                    f"🏢 Поставщик: {delivery['supplier']}\n"
                    f"🏗️ Объект: {delivery['object_name']}\n"
                    f"👤 Поставщик: {delivery['seller_name']}\n"
                    f"👤 Заказчик: {delivery['buyer_name']}\n"
                    f"💵 Сумма: {delivery['total_amount']:,} сум\n"
                    f"📅 Время: {get_current_time()}\n\n"
                    f"✅ Илтимос, товарларни текширинг ва тўғридаги тугмани босинг:",
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Failed to notify warehouse user {warehouse_user['telegram_id']}: {e}")
        
        # Обновляем сообщение поставщика
        await callback_query.message.edit_text(
            f"🚚 **Товарлар юборилди!**\n\n"
            f"📦 Доставка #{delivery_id}\n"
            f"📅 Время отправки: {get_current_time()}\n\n"
            f"✅ Склад ходимларига хабар юборилди. Улар товарларни текшириб, тасдиқлашади."
        )
        await callback_query.answer("✅ Отправка подтверждена!")
        
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка: {str(e)}")

# Обработчик текстовых сообщений
@router.message()
async def handle_text(message: types.Message, state: FSMContext):
    """Обработка текстовых сообщений"""
    # Проверяем, не находится ли пользователь в процессе регистрации
    current_state = await state.get_state()
    if current_state and current_state.startswith('RegistrationStates'):
        # Если пользователь в процессе регистрации, не обрабатываем команды меню
        return
    
    user = db.get_user(message.from_user.id)
    
    if not user or not user['is_approved']:
        await message.answer("Илтимос, аввал /register ёрдамида рўйхатдан ўтинг")
        return
    
    # Проверяем, является ли это командой меню
    text = message.text
    menu_commands = [
        "ℹ️ Ёрдам",
        "📋 Ариза яратиш", 
        "📊 Менинг аризаларим",
        "📦 Менинг буюртмаларим",
        "📋 Фаол аризалар",
        "💼 Менинг таклифларим",
        "📦 Кутган етказиб беришлар"
    ]
    
    # Если это команда меню, обрабатываем её
    if text in menu_commands:
        if text == "ℹ️ Ёрдам":
            await show_help(message, user['role'])
        elif text == "📋 Ариза яратиш" and user['role'] == 'buyer':
            await start_purchase_request(message, state)
        elif text == "📊 Менинг аризаларим" and user['role'] == 'buyer':
            await show_my_requests(message)
        elif text == "📦 Менинг буюртмаларим" and user['role'] == 'buyer':
            await show_my_orders(message)
        elif text == "📋 Фаол аризалар" and user['role'] == 'seller':
            await show_active_requests(message)
        elif text == "💼 Менинг таклифларим" and user['role'] == 'seller':
            await show_my_offers(message)
        elif text == "📦 Кутган етказиб беришлар" and user['role'] == 'warehouse':
            await show_pending_deliveries(message)
        elif text == "✅ Қабул қилинган товарлар" and user['role'] == 'warehouse':
            await show_received_deliveries(message)
        else:
            await message.answer("❌ У вас нет прав для этой функции.")
        return
    


async def show_help(message: types.Message, role: str):
    """Показать справку"""
    help_text = "📚 Ботдан фойдаланиш бўйича маълумот:\n\n"
    
    if role == 'buyer':
        help_text += "👤 Заказчик:\n"
        help_text += "• Товар сотиб олиш учун аризалар яратинг\n"
        help_text += "• Поставщиклардан таклифлар олинг\n"
        help_text += "• Буюртмалар статусини кузатинг\n\n"
    elif role == 'seller':
        help_text += "🏪 Поставщик:\n"
        help_text += "• Фаол аризаларни кўринг\n"
        help_text += "• Заказчикларга таклифлар юборинг\n"
        help_text += "• Ўзингизнинг таклифларингизни кузатинг\n\n"
    elif role == 'warehouse':
        help_text += "🏭 Зав. Склад:\n"
        help_text += "• Поставщиклардан товарларни қабул қилинг\n"
        help_text += "• Товарларни олишни тасдиқланг\n"
        help_text += "• Заказчикларни хабардор қилинг\n\n"
    
    help_text += "⏰ Вақт: " + get_current_time()
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
        await message.answer("❌ Фақат заказчиклар аризаларни кўра олади.")
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
        await message.answer("📭 Ҳозирча аризаларингиз йўқ.")
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
        await message.answer("❌ Фақат поставщиклар фаол аризаларни кўра олади.")
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
        await message.answer("📭 Фаол аризалар йўқ.")
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
        await message.answer("❌ Фақат заказчиклар буюртмаларни кўра олади.")
        return
    
    # Получаем одобренные предложения
    approved_offers = db.get_approved_offers_for_buyer(user['id'])
    
    if not approved_offers:
        await message.answer("📭 Ҳозирча тасдиқланган буюртмаларингиз йўқ.")
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

async def show_my_offers(message: types.Message):
    """Показать предложения поставщика"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'seller':
        await message.answer("❌ Фақат поставщиклар ўз таклифларини кўра олади.")
        return
    
    # Получаем предложения пользователя
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT so.*, pr.supplier, pr.object_name
        FROM seller_offers so
        JOIN purchase_requests pr ON so.purchase_request_id = pr.id
        WHERE so.seller_id = %s 
        ORDER BY so.created_at DESC
    """, (user['id'],))
    offers = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    if not offers:
        await message.answer("📭 Ҳозирча таклифларингиз йўқ.")
        return
    
    for offer in offers[:5]:  # Показываем последние 5 предложений
        status_text = {
            'pending': '⏳ Кутмоқда',
            'approved': '✅ Тасдиқланган',
            'rejected': '❌ Рад этилган'
        }.get(offer['status'], '❓ Номаълум')
        
        text = f"💼 **Таклиф #{offer['id']}**\n\n"
        text += f"🏢 Поставщик: {offer['supplier']}\n"
        text += f"🏗️ Объект: {offer['object_name']}\n"
        text += f"💵 Умумий сумма: {offer['total_amount']:,} сўм\n"
        text += f"📊 Статус: {status_text}\n"
        text += f"📅 Сана: {offer['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        
        await message.answer(text)

async def show_pending_deliveries(message: types.Message):
    """Показать ожидающие доставки для склада"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        await message.answer("❌ Фақат склад ходимлари етказиб беришларни кўра олади.")
        return
    
    # Получаем ожидающие доставки
    deliveries = db.get_pending_deliveries()
    
    if not deliveries:
        await message.answer("📭 Ҳозирча кутган етказиб беришлар йўқ.")
        return
    
    await message.answer(f"📦 Кутган етказиб беришлар: {len(deliveries)} та")
    
    for delivery in deliveries[:10]:  # Показываем последние 10 доставок
        text = f"📦 **Етказиб бериш #{delivery['id']}**\n\n"
        text += f"🏢 Поставщик: {delivery['supplier']}\n"
        text += f"🏗️ Объект: {delivery['object_name']}\n"
        text += f"👤 Поставщик: {delivery['seller_name']}\n"
        text += f"📞 Телефон поставщика: {delivery['seller_phone']}\n"
        text += f"👤 Заказчик: {delivery['buyer_name']}\n"
        text += f"📞 Телефон заказчика: {delivery['buyer_phone']}\n"
        text += f"💵 Общая сумма: {delivery['total_amount']:,} сум\n"
        text += f"📅 Дата создания: {delivery['created_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Добавляем кнопки для управления доставкой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Доставлено", callback_data=f"deliver_{delivery['id']}"),
                InlineKeyboardButton(text="📞 Связаться с поставщиком", callback_data=f"contact_seller_{delivery['seller_phone']}")
            ],
            [
                InlineKeyboardButton(text="📞 Связаться с заказчиком", callback_data=f"contact_buyer_{delivery['buyer_phone']}")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard)

async def show_received_deliveries(message: types.Message):
    """Показать принятые доставки для склада"""
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'warehouse':
        await message.answer("❌ Фақат склад ходимлари қабул қилинган товарларни кўра олади.")
        return
    
    # Получаем принятые доставки
    deliveries = db.get_received_deliveries()
    
    if not deliveries:
        await message.answer("📭 Ҳозирча қабул қилинган товарлар йўқ.")
        return
    
    await message.answer(f"✅ Қабул қилинган товарлар: {len(deliveries)} та")
    
    for delivery in deliveries[:10]:  # Показываем последние 10 доставок
        text = f"✅ **Қабул қилинган товарлар #{delivery['id']}**\n\n"
        text += f"🏢 Поставщик: {delivery['supplier']}\n"
        text += f"🏗️ Объект: {delivery['object_name']}\n"
        text += f"👤 Поставщик: {delivery['seller_name']}\n"
        text += f"👤 Заказчик: {delivery['buyer_name']}\n"
        text += f"💵 Общая сумма: {delivery['total_amount']:,} сум\n"
        text += f"📅 Дата принятия: {delivery['received_at'].strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Детали товаров
        text += "📋 **Товары:**\n"
        for i, item in enumerate(delivery['items'], 1):
            text += f"{i}. {item['product_name']}\n"
            text += f"   📊 Количество: {item['quantity']} {item['unit']}\n"
            text += f"   💰 Цена за единицу: {item['price_per_unit']:,} сум\n"
            text += f"   💵 Сумма: {item['total_price']:,} сум\n"
            if item['material_description']:
                text += f"   📝 Описание: {item['material_description']}\n"
            text += "\n"
        
        await message.answer(text)

# Запуск бота
async def main():
    """Главная функция"""
    # Создание таблиц базы данных
    db.create_tables()
    
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 