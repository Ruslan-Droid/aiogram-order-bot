from datetime import datetime
from types import NoneType
from typing import Dict, Any
from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.enums.cart_statuses import CartStatus
from app.infrastructure.database.enums.order_statuses import OrderStatus
from app.infrastructure.database.models import DeliveryOrderModel, CartModel
from app.infrastructure.database.query.cart_queries import CartRepository
from app.infrastructure.database.query.order_queries import OrderRepository


async def get_cart_data(
        dialog_manager: DialogManager,
        session: AsyncSession,
        user_row,
        **kwargs
) -> Dict[str, Any]:
    try:
        cart_id = dialog_manager.start_data["cart_id"]
    except:
        cart_id = None

    # Если cart_id не передан, получаем текущую корзину пользователя
    if not cart_id:
        cart: CartModel = await CartRepository(session).get_current_cart(user_row.id)

        if cart:
            cart_id = cart.id
            dialog_manager.dialog_data["cart_id"] = cart_id
        else:
            return {
                "cart_items": "Пусто",
                "total_amount": 0.0,
                "cart": None,
                "restaurant_name": "",
                "cart_status": "Пустая",
                "is_attachable": False,
                "note": "Не указан"
            }
    else:
        cart: CartModel = await CartRepository(session).get_cart_by_id(cart_id)

    text_with_items = ""
    total_price = 0.0

    for item in cart.item_associations:
        dish_name = item.dish.name
        amount = item.amount
        price = item.amount * item.price_at_time

        text_with_items += f"{dish_name} - {amount} Шт. - {price}₽\n"
        total_price += price

    # Определяем статус корзины для отображения
    return {
        "cart_items": text_with_items,
        "total_price": total_price,
        "restaurant_name": cart.restaurant.name if cart.restaurant else "",
        "cart_status": cart.status.value,
        "is_attachable": cart.status == CartStatus.ACTIVE and total_price > 0,
        "note": cart.notes if cart.notes else "не указан",
    }


async def get_active_orders_for_adding_cart(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    active_orders: list[DeliveryOrderModel] = await OrderRepository(session).get_orders_by_date(
        order_date=datetime.today(), status=OrderStatus.COLLECTING)

    return {
        "orders": [
            (f"{order.restaurant.name} - {order.status.value} - {order.created_at.date()}", order.id) for order in
            active_orders
        ],
        "orders_count": len(active_orders),
    }


async def get_comment_data(
        dialog_manager: DialogManager,
        **kwargs
) -> Dict[str, Any]:
    cart = dialog_manager.dialog_data.get("cart")
    current_comment = cart.notes if hasattr(cart, 'notes') and cart.notes else "не указан"

    return {
        "current_comment": current_comment
    }

    # Для доставщика, чтобы посмотреть все корзины заказа


async def get_order_carts_summary(
        self,
        order_id: int
) -> dict:
    """Получает сводную информацию по всем корзинам заказа"""
    carts = await self.get_carts_by_order(order_id)

    summary = {
        "total_amount": 0,
        "total_items": 0,
        "carts": [],
        "users": []
    }

    for cart in carts:
        user_info = {
            "user_id": cart.user_id,
            "username": cart.user.username or cart.user.full_name,
            "total": cart.total_amount,
            "items_count": cart.items_count,
            "notes": cart.notes
        }

        summary["total_amount"] += cart.total_amount
        summary["total_items"] += cart.items_count
        summary["users"].append(user_info)

        # Детали по позициям
        cart_details = []
        for item in cart.item_associations:
            cart_details.append({
                "dish_name": item.dish.name,
                "amount": item.amount,
                "price": item.price_at_time,
                "total": item.amount * item.price_at_time
            })
        summary["carts"].append({
            "user": user_info,
            "items": cart_details
        })

    return summary
