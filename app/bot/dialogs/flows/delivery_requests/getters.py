from datetime import datetime

from aiogram_dialog import DialogManager

from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.query.restaurant_queries import RestaurantRepository
from app.infrastructure.database.query.order_queries import OrderRepository


async def get_restaurants(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data["session"]

    restaurants = await RestaurantRepository(session).get_all_active_restaurants()

    restaurants_list = [
        {"id": rest.id, "name": rest.name} for rest in restaurants
    ]

    # Сохраняем список в dialog_data для использования в обработчике
    dialog_manager.dialog_data["_restaurants_cache"] = restaurants_list

    return {"restaurants": restaurants_list}


async def get_today_orders(dialog_manager: DialogManager, **kwargs) -> dict:
    session = dialog_manager.middleware_data["session"]
    user: UserModel = dialog_manager.middleware_data["user_row"]

    today = datetime.now().today()

    orders = await OrderRepository(session).get_orders_by_date(today)

    # Фильтрация по правам
    if user.role == UserRole.DELIVERY:
        orders = [order for order in orders if order.creator_id == user.id]

    return {"orders": [(f"Заявка #{order.id}", order.id) for order in orders]}


async def getter_create_enter_contact(dialog_manager: DialogManager, **kwargs) -> dict:
    user: UserModel = dialog_manager.middleware_data["user_row"]

    return {"number": user.phone_number}


async def getter_select_bank(
        dialog_manager: DialogManager,
        **kwargs
) -> dict:
    # Получаем предпочтительный банк пользователя из БД
    user: UserModel = dialog_manager.middleware_data.get("user_row")
    preferred_bank = None
    if user.preferred_bank:
        preferred_bank = user.preferred_bank

    # Создаем список банков в формате (id, display_name)
    banks_list = [
        (method.value, method.value)  # (значение Enum, отображаемое имя)
        for method in PaymentMethod
    ]

    return {
        "banks": banks_list,
        "preferred_bank": preferred_bank
    }
