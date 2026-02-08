from datetime import datetime

from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.enums.payment_methods import PaymentMethod
from app.infrastructure.database.enums.user_roles import UserRole
from app.infrastructure.database.models import UserModel, RestaurantModel
from app.infrastructure.database.query.restaurant_queries import RestaurantRepository
from app.infrastructure.database.query.order_queries import OrderRepository


async def get_restaurants(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> dict:
    restaurants: list[RestaurantModel] = await RestaurantRepository(session).get_all_active_restaurants()

    restaurants_list = [
        {"id": rest.id, "name": rest.name} for rest in restaurants
    ]

    # Сохраняем список в dialog_data для использования в обработчике
    dialog_manager.dialog_data["_restaurants_cache"] = restaurants_list

    return {"restaurants": restaurants_list}


async def getter_create_enter_contact(
        dialog_manager: DialogManager,
        user_row: UserModel,
        **kwargs
) -> dict:
    dialog_manager.dialog_data["phone"] = user_row.phone_number

    return {"number": user_row.phone_number}


async def getter_select_bank(
        dialog_manager: DialogManager,
        user_row: UserModel,
        **kwargs
) -> dict:
    # Получаем предпочтительный банк пользователя из БД
    preferred_bank = None
    if user_row.preferred_bank:
        preferred_bank = user_row.preferred_bank
        dialog_manager.dialog_data["bank"] = preferred_bank

    # Создаем список банков в формате (id, display_name)
    banks_list = [
        (method.value, method.value)  # (значение Enum, отображаемое имя)
        for method in PaymentMethod
    ]

    return {
        "banks": banks_list,
        "preferred_bank": preferred_bank.value
    }


async def getter_confirm_create(
        dialog_manager: DialogManager,
        **kwargs
) -> dict:
    phone = dialog_manager.dialog_data["phone"]
    bank = dialog_manager.dialog_data["bank"]
    restaurant_name = dialog_manager.dialog_data["restaurant_name"]
    comment = dialog_manager.dialog_data.get("comment", "пустой")

    return {
        "phone": phone,
        "bank": bank,
        "restaurant_name": restaurant_name,
        "comment": comment
    }


async def get_today_orders(
        dialog_manager: DialogManager,
        session: AsyncSession,
        user_row: UserModel,
        **kwargs
) -> dict:
    today = datetime.now().today()

    orders = await OrderRepository(session).get_orders_by_date(today)

    # Фильтрация по правам
    if user_row.role == UserRole.DELIVERY:
        orders = [order for order in orders if order.creator_id == user_row.id]

    return {"orders": [(f"Заявка #{order.id} - {order.status.value}", order.id) for order in orders]}


async def get_order_statuses(
        dialog_manager: DialogManager,
        **kwargs
) -> dict:
    return {
        "statuses": [
            (status.value, status.name)
            for status in OrderStatus
        ]
    }
