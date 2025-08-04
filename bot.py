import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import FSInputFile

from config import BOT_TOKEN, ROLES, OFFER_STATUSES
from database import Database
from keyboards import *
from states import *
from utils import *

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()

# Словарь для хранения временных данных пользователей
user_data = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    user = await db.get_user(message.from_user.id)
    
    if user is None:
        # Новый пользователь - регистрация
        await message.answer(
            "👋 Добро пожаловать в систему закупок SFX!\n\n"
            "Для начала работы необходимо зарегистрироваться.\n"
            "Введите ваше полное имя:"
        )
        await state.set_state(RegistrationStates.waiting_for_name)
    else:
        # Существующий пользователь
        if user['is_approved']:
            await show_main_menu(message)
        else:
            await message.answer(
                "⏳ Ваша регистрация находится на рассмотрении администратора.\n"
                "Ожидайте одобрения для доступа к системе."
            )

@dp.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    await state.update_data(name=message.text)
    await message.answer(
        "📞 Теперь введите ваш номер телефона в формате:\n"
        "+998XXXXXXXXX или 998XXXXXXXXX"
    )
    await state.set_state(RegistrationStates.waiting_for_phone)

@dp.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = validate_phone_number(message.text)
    if phone is None:
        await message.answer(
            "❌ Неверный формат номера телефона!\n"
            "Пожалуйста, введите номер в формате:\n"
            "+998XXXXXXXXX или 998XXXXXXXXX"
        )
        return
    
    await state.update_data(phone=phone)
    await message.answer(
        "👤 Выберите вашу роль в системе:",
        reply_markup=get_role_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_role)

@dp.message(RegistrationStates.waiting_for_role)
async def process_role(message: types.Message, state: FSMContext):
    """Обработка выбора роли"""
    role_map = {
        "👤 Покупатель": "buyer",
        "🏪 Продавец": "seller", 
        "🏭 Человек на складе": "warehouse"
    }
    
    if message.text not in role_map:
        await message.answer("❌ Пожалуйста, выберите роль из предложенных вариантов.")
        return
    
    role = role_map[message.text]
    user_data = await state.get_data()
    
    # Создание пользователя в базе данных
    try:
        await db.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=user_data['name'],
            phone_number=user_data['phone'],
            role=role
        )
        
        if role == "seller":
            # Продавцы не требуют одобрения
            await db.approve_user(message.from_user.id)
            await message.answer(
                "✅ Регистрация успешно завершена!\n"
                "Теперь вы можете использовать систему.",
                reply_markup=get_main_keyboard()
            )
        else:
            # Покупатели и люди на складе требуют одобрения
            await message.answer(
                "✅ Регистрация успешно завершена!\n"
                "⏳ Ожидайте одобрения администратора для доступа к системе."
            )
            
            # Уведомление администраторов
            await notify_admins_new_user(message.from_user.id, user_data['name'], role)
            
    except Exception as e:
        await message.answer("❌ Ошибка при регистрации. Попробуйте позже.")
        logging.error(f"Registration error: {e}")

async def notify_admins_new_user(telegram_id, name, role):
    """Уведомление администраторов о новом пользователе"""
    # Здесь нужно получить всех администраторов из базы данных
    # Пока используем хардкод
    admin_ids = [123456789]  # Замените на реальные ID администраторов
    
    for admin_id in admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"👤 Новый пользователь ожидает одобрения:\n\n"
                f"Имя: {name}\n"
                f"Роль: {ROLES.get(role, role)}\n"
                f"ID: {telegram_id}",
                reply_markup=get_approval_keyboard(telegram_id)
            )
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")

@dp.message(lambda message: message.text == "📋 Создать заявку")
async def create_request(message: types.Message):
    """Создание заявки на покупку"""
    user = await db.get_user(message.from_user.id)
    if user['role'] != 'buyer':
        await message.answer("❌ Только покупатели могут создавать заявки.")
        return
    
    await message.answer(
        "📋 Выберите формат заявки:",
        reply_markup=get_request_type_keyboard()
    )
    await state.set_state(RequestStates.waiting_for_request_type)

@dp.message(RequestStates.waiting_for_request_type)
async def process_request_type(message: types.Message, state: FSMContext):
    """Обработка выбора типа заявки"""
    if message.text == "📊 Excel файл":
        # Создаем шаблон Excel
        excel_file = create_excel_template()
        await message.answer_document(
            FSInputFile(excel_file, filename="заявка_шаблон.xlsx"),
            caption="📊 Заполните этот шаблон и отправьте обратно:"
        )
        await state.set_state(RequestStates.waiting_for_excel_file)
        
    elif message.text == "📝 Текстовый формат":
        await message.answer(
            "📝 Введите данные заявки в текстовом формате.\n\n"
            "Формат:\n"
            "Поставщик: [название поставщика]\n"
            "Объект: [название объекта]\n"
            "Товар: [название товара]\n"
            "Количество: [число]\n"
            "Единица: [шт/кг/м и т.д.]\n"
            "Описание: [дополнительная информация]"
        )
        await state.set_state(RequestStates.waiting_for_text_request)
        
    elif message.text == "🔙 Назад":
        await show_main_menu(message)
    else:
        await message.answer("❌ Пожалуйста, выберите формат из предложенных вариантов.")

@dp.message(RequestStates.waiting_for_excel_file, F.content_type == "document")
async def process_excel_request(message: types.Message, state: FSMContext):
    """Обработка Excel файла с заявкой"""
    try:
        # Скачиваем файл
        file = await bot.get_file(message.document.file_id)
        file_content = await bot.download_file(file.file_path)
        
        # Парсим Excel
        requests = parse_excel_request(file_content.read())
        
        if not requests:
            await message.answer("❌ Файл пуст или имеет неверный формат.")
            return
        
        # Сохраняем заявки в базе данных
        user = await db.get_user(message.from_user.id)
        for request_data in requests:
            await db.create_purchase_request(
                buyer_id=user['id'],
                supplier=request_data['supplier'],
                object_name=request_data['object_name'],
                product_name=request_data['product_name'],
                quantity=request_data['quantity'],
                unit=request_data['unit'],
                material_description=request_data['material_description'],
                request_type='excel'
            )
        
        # Отправляем всем продавцам
        sellers = await db.get_sellers()
        for seller in sellers:
            try:
                await bot.send_message(
                    seller['telegram_id'],
                    f"📋 Новая заявка на покупку!\n\n{format_request_text(requests[0])}"
                )
            except Exception as e:
                logging.error(f"Failed to send request to seller {seller['telegram_id']}: {e}")
        
        await message.answer(
            f"✅ Заявка успешно создана и отправлена {len(sellers)} продавцам!",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")

@dp.message(RequestStates.waiting_for_text_request)
async def process_text_request(message: types.Message, state: FSMContext):
    """Обработка текстовой заявки"""
    # Простой парсинг текста (можно улучшить)
    text = message.text.lower()
    
    # Извлекаем данные из текста
    supplier = extract_value(text, "поставщик:")
    object_name = extract_value(text, "объект:")
    product_name = extract_value(text, "товар:")
    quantity = extract_value(text, "количество:")
    unit = extract_value(text, "единица:")
    description = extract_value(text, "описание:")
    
    if not all([supplier, object_name, product_name, quantity]):
        await message.answer(
            "❌ Не все обязательные поля заполнены.\n"
            "Пожалуйста, укажите: поставщик, объект, товар, количество."
        )
        return
    
    # Сохраняем в базе данных
    user = await db.get_user(message.from_user.id)
    await db.create_purchase_request(
        buyer_id=user['id'],
        supplier=supplier,
        object_name=object_name,
        product_name=product_name,
        quantity=float(quantity),
        unit=unit,
        material_description=description,
        request_type='text'
    )
    
    # Отправляем всем продавцам
    sellers = await db.get_sellers()
    for seller in sellers:
        try:
            request_data = {
                'buyer': user['full_name'],
                'supplier': supplier,
                'object_name': object_name,
                'product_name': product_name,
                'quantity': quantity,
                'unit': unit,
                'material_description': description
            }
            message_text = f"📋 Новая заявка на покупку!\n\n{format_request_text(request_data)}"
            await bot.send_message(seller['telegram_id'], message_text)
        except Exception as e:
            logging.error(f"Failed to send request to seller {seller['telegram_id']}: {e}")
    
    await message.answer(
        f"✅ Заявка успешно создана и отправлена {len(sellers)} продавцам!",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

def extract_value(text, key):
    """Извлечение значения из текста по ключу"""
    try:
        start = text.find(key) + len(key)
        end = text.find('\n', start)
        if end == -1:
            end = len(text)
        return text[start:end].strip()
    except:
        return ""

@dp.message(lambda message: message.text == "📊 Мои заявки")
async def show_my_requests(message: types.Message):
    """Показать заявки пользователя"""
    user = await db.get_user(message.from_user.id)
    if user['role'] != 'buyer':
        await message.answer("❌ Только покупатели могут просматривать заявки.")
        return
    
    requests = await db.get_purchase_requests_for_buyer(user['id'])
    
    if not requests:
        await message.answer("📭 У вас пока нет заявок.")
        return
    
    for req in requests[:5]:  # Показываем последние 5 заявок
        offers = await db.get_offers_for_request(req['id'])
        
        text = f"""
📋 **Заявка #{req['id']}**

🏢 **Поставщик:** {req['supplier']}
🏗️ **Объект:** {req['object_name']}
📦 **Товар:** {req['product_name']}
📊 **Количество:** {req['quantity']} {req['unit']}
📝 **Описание:** {req['material_description']}
📅 **Дата:** {req['created_at'].strftime('%d.%m.%Y %H:%M')}

💰 **Предложений:** {len(offers)}
"""
        
        if offers:
            text += "\n**Последние предложения:**\n"
            for offer in offers[:3]:
                text += f"• {offer['full_name']}: {offer['price']} сум\n"
        
        await message.answer(text)

@dp.message(lambda message: message.text == "💰 Мои предложения")
async def show_my_offers(message: types.Message):
    """Показать предложения продавца"""
    user = await db.get_user(message.from_user.id)
    if user['role'] != 'seller':
        await message.answer("❌ Только продавцы могут просматривать предложения.")
        return
    
    # Получаем предложения продавца
    offers = await db.get_seller_offers(user['id'])
    
    if not offers:
        await message.answer("📭 У вас пока нет предложений.")
        return
    
    for offer in offers[:5]:
        text = f"""
💰 **Предложение #{offer['id']}**

💵 **Цена:** {offer['price']} сум
💸 **Сумма:** {offer['total_amount']} сум
📅 **Дата:** {offer['created_at'].strftime('%d.%m.%Y %H:%M')}
📊 **Статус:** {OFFER_STATUSES.get(offer['status'], offer['status'])}
"""
        await message.answer(text)

@dp.message(lambda message: message.text == "📦 Доставки")
async def show_deliveries(message: types.Message):
    """Показать доставки"""
    user = await db.get_user(message.from_user.id)
    if user['role'] not in ['buyer', 'warehouse']:
        await message.answer("❌ Только покупатели и люди на складе могут просматривать доставки.")
        return
    
    if user['role'] == 'warehouse':
        # Показываем ожидающие доставки
        deliveries = await db.get_pending_deliveries()
        
        if not deliveries:
            await message.answer("📭 Нет ожидающих доставок.")
            return
        
        for delivery in deliveries:
            text = f"""
📦 **Доставка #{delivery['id']}**

👤 **Продавец:** {delivery['seller_name']}
📞 **Телефон:** {delivery['seller_phone']}
💵 **Сумма:** {delivery['total_amount']} сум
📅 **Дата:** {delivery['created_at'].strftime('%d.%m.%Y %H:%M')}
"""
            await message.answer(
                text,
                reply_markup=get_delivery_keyboard(delivery['id'])
            )

@dp.callback_query(lambda c: c.data.startswith('received_'))
async def process_delivery_received(callback: types.CallbackQuery):
    """Обработка подтверждения получения товара"""
    delivery_id = int(callback.data.split('_')[1])
    
    try:
        await db.mark_delivery_received(delivery_id)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ **ТОВАР ПОЛУЧЕН НА СКЛАДЕ**"
        )
        
        # Уведомляем покупателя
        delivery = await db.get_delivery_info(delivery_id)
        if delivery:
            await bot.send_message(
                delivery['buyer_telegram_id'],
                "📦 Товар получен на складе и готов к использованию!"
            )
            
    except Exception as e:
        await callback.answer("❌ Ошибка при обновлении статуса")
        logging.error(f"Delivery received error: {e}")

@dp.callback_query(lambda c: c.data.startswith('approve_'))
async def process_user_approval(callback: types.CallbackQuery):
    """Обработка одобрения пользователя"""
    user_id = int(callback.data.split('_')[1])
    
    try:
        await db.approve_user(user_id)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ **ОДОБРЕНО**"
        )
        
        # Уведомляем пользователя
        await bot.send_message(
            user_id,
            "✅ Ваша регистрация одобрена! Теперь вы можете использовать систему.",
            reply_markup=get_main_keyboard()
        )
        
    except Exception as e:
        await callback.answer("❌ Ошибка при одобрении")
        logging.error(f"User approval error: {e}")

@dp.callback_query(lambda c: c.data.startswith('reject_'))
async def process_user_rejection(callback: types.CallbackQuery):
    """Обработка отклонения пользователя"""
    user_id = int(callback.data.split('_')[1])
    
    try:
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ **ОТКЛОНЕНО**"
        )
        
        # Уведомляем пользователя
        await bot.send_message(
            user_id,
            "❌ Ваша регистрация отклонена. Обратитесь к администратору."
        )
        
    except Exception as e:
        await callback.answer("❌ Ошибка при отклонении")
        logging.error(f"User rejection error: {e}")

async def show_main_menu(message: types.Message):
    """Показать главное меню"""
    user = await db.get_user(message.from_user.id)
    
    if user['role'] == 'admin':
        await message.answer(
            "👨‍💼 Панель администратора",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.answer(
            f"👋 Добро пожаловать, {user['full_name']}!\n"
            f"Роль: {ROLES.get(user['role'], user['role'])}",
            reply_markup=get_main_keyboard()
        )

async def main():
    """Главная функция"""
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 