from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    """Состояния для регистрации"""
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_role = State()
    waiting_for_object = State()
    waiting_for_location = State()

class RequestStates(StatesGroup):
    """Состояния для создания заявки"""
    waiting_for_request_type = State()
    waiting_for_excel_file = State()
    waiting_for_text_request = State()
    waiting_for_supplier = State()
    waiting_for_object_name = State()
    waiting_for_product_name = State()
    waiting_for_quantity = State()
    waiting_for_unit = State()
    waiting_for_description = State()

class OfferStates(StatesGroup):
    """Состояния для создания предложения"""
    waiting_for_offer_type = State()
    waiting_for_excel_offer = State()
    waiting_for_text_offer = State()
    waiting_for_price = State()
    waiting_for_total_amount = State()

class AdminStates(StatesGroup):
    """Состояния для администратора"""
    waiting_for_admin_action = State() 