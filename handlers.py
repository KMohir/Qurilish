import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from database import Database
from keyboards import *
from states import *
from utils import *
from config import ROLES, OFFER_STATUSES

db = Database()

async def handle_seller_offer(message: types.Message, state: FSMContext):
    """Обработка предложения от продавца"""
    user = await db.get_user(message.from_user.id)
    if user['role'] != 'seller':
        await message.answer("❌ Только продавцы могут отправлять предложения.")
        return
    
    await message.answer(
        "💰 Выберите формат предложения:",
        reply_markup=get_offer_type_keyboard()
    )
    await state.set_state(OfferStates.waiting_for_offer_type)

async def process_offer_type(message: types.Message, state: FSMContext):
    """Обработка выбора типа предложения"""
    if message.text == "📊 Excel файл":
        excel_file = create_offer_excel_template()
        await message.answer_document(
            FSInputFile(excel_file, filename="предложение_шаблон.xlsx"),
            caption="📊 Заполните этот шаблон и отправьте обратно:"
        )
        await state.set_state(OfferStates.waiting_for_excel_offer)
        
    elif message.text == "📝 Текстовый формат":
        await message.answer(
            "📝 Введите данные предложения в текстовом формате.\n\n"
            "Формат:\n"
            "Цена: [цена за единицу]\n"
            "Сумма: [общая сумма]"
        )
        await state.set_state(OfferStates.waiting_for_text_offer)
        
    elif message.text == "🔙 Назад":
        await show_main_menu(message)
    else:
        await message.answer("❌ Пожалуйста, выберите формат из предложенных вариантов.")

async def process_excel_offer(message: types.Message, state: FSMContext):
    """Обработка Excel файла с предложением"""
    try:
        # Скачиваем файл
        file = await message.bot.get_file(message.document.file_id)
        file_content = await message.bot.download_file(file.file_path)
        
        # Парсим Excel
        offers = parse_excel_offer(file_content.read())
        
        if not offers:
            await message.answer("❌ Файл пуст или имеет неверный формат.")
            return
        
        # Сохраняем предложения в базе данных
        user = await db.get_user(message.from_user.id)
        for offer_data in offers:
            await db.create_seller_offer(
                purchase_request_id=1,  # Нужно получить из контекста
                seller_id=user['id'],
                price=offer_data['price'],
                total_amount=offer_data['total_amount'],
                offer_type='excel'
            )
        
        await message.answer(
            "✅ Предложение успешно отправлено!",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {str(e)}")

async def process_text_offer(message: types.Message, state: FSMContext):
    """Обработка текстового предложения"""
    text = message.text.lower()
    
    price = extract_value(text, "цена:")
    total_amount = extract_value(text, "сумма:")
    
    if not all([price, total_amount]):
        await message.answer(
            "❌ Не все обязательные поля заполнены.\n"
            "Пожалуйста, укажите: цена, сумма."
        )
        return
    
    # Сохраняем в базе данных
    user = await db.get_user(message.from_user.id)
    await db.create_seller_offer(
        purchase_request_id=1,  # Нужно получить из контекста
        seller_id=user['id'],
        price=float(price),
        total_amount=float(total_amount),
        offer_type='text'
    )
    
    await message.answer(
        "✅ Предложение успешно отправлено!",
        reply_markup=get_main_keyboard()
    )
    await state.clear()

async def handle_admin_panel(message: types.Message):
    """Обработка панели администратора"""
    user = await db.get_user(message.from_user.id)
    if user['role'] != 'admin':
        await message.answer("❌ Доступ запрещен.")
        return
    
    if message.text == "👥 Пользователи на одобрении":
        await show_pending_users(message)
    elif message.text == "📊 Статистика":
        await show_statistics(message)
    elif message.text == "🔙 Главное меню":
        await show_main_menu(message)

async def show_pending_users(message: types.Message):
    """Показать пользователей ожидающих одобрения"""
    pending_users = await db.get_pending_users()
    
    if not pending_users:
        await message.answer("✅ Нет пользователей ожидающих одобрения.")
        return
    
    for user in pending_users:
        text = f"""
👤 **Пользователь ожидает одобрения**

📝 **Имя:** {user['full_name']}
📞 **Телефон:** {user['phone_number']}
👤 **Роль:** {ROLES.get(user['role'], user['role'])}
📅 **Дата регистрации:** {user['created_at'].strftime('%d.%m.%Y %H:%M')}
"""
        await message.answer(
            text,
            reply_markup=get_approval_keyboard(user['telegram_id'])
        )

async def show_statistics(message: types.Message):
    """Показать статистику"""
    # Здесь можно добавить получение статистики из базы данных
    stats_text = """
📊 **Статистика системы**

👥 **Пользователи:**
• Всего: [количество]
• Покупатели: [количество]
• Продавцы: [количество]
• Люди на складе: [количество]

📋 **Заявки:**
• Всего: [количество]
• Активные: [количество]
• Завершенные: [количество]

💰 **Предложения:**
• Всего: [количество]
• Одобренные: [количество]
• Ожидающие: [количество]

📦 **Доставки:**
• Всего: [количество]
• Полученные: [количество]
• Ожидающие: [количество]
"""
    await message.answer(stats_text)

async def handle_offer_approval(callback: types.CallbackQuery):
    """Обработка одобрения предложения"""
    offer_id = int(callback.data.split('_')[2])
    
    try:
        await db.approve_offer(offer_id)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ **ОДОБРЕНО**"
        )
        
        # Уведомляем продавца
        offer = await db.get_offer_info(offer_id)
        if offer:
            await callback.bot.send_message(
                offer['seller_telegram_id'],
                "✅ Ваше предложение одобрено покупателем!"
            )
            
    except Exception as e:
        await callback.answer("❌ Ошибка при одобрении")
        logging.error(f"Offer approval error: {e}")

async def handle_offer_rejection(callback: types.CallbackQuery):
    """Обработка отклонения предложения"""
    offer_id = int(callback.data.split('_')[2])
    
    try:
        await db.reject_offer(offer_id)
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ **ОТКЛОНЕНО**"
        )
        
        # Уведомляем продавца
        offer = await db.get_offer_info(offer_id)
        if offer:
            await callback.bot.send_message(
                offer['seller_telegram_id'],
                "❌ Ваше предложение отклонено покупателем."
            )
            
    except Exception as e:
        await callback.answer("❌ Ошибка при отклонении")
        logging.error(f"Offer rejection error: {e}")

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