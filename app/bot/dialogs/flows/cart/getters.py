from datetime import datetime
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
    cart: CartModel = await CartRepository(session).get_current_cart(user_row.id)

    if cart:
        cart_id = cart.id
        dialog_manager.dialog_data["cart_id"] = cart_id
    else:
        return {
            "restaurant_name": "",
            "cart_status": "Пустая",
            "cart_items": "Пусто",
            "total_price": 0.0,
            "is_attachable": False,
            "note": "Не указан"
        }

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


async def get_comment_data(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    cart_id = dialog_manager.dialog_data["cart_id"]
    cart: CartModel = await CartRepository(session).get_cart_by_id(cart_id)

    return {
        "current_comment": cart.notes if cart.notes else "Не указан",
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


async def get_cart_items_for_edit(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    """Получает список блюд в корзине для редактирования"""
    cart_id = dialog_manager.dialog_data.get("cart_id")
    cart = await CartRepository(session).get_cart_by_id(cart_id)

    if not cart or not cart.item_associations:
        return {
            "cart_items": [],
            "cart_empty": True,
            "restaurant_name": cart.restaurant.name if cart and cart.restaurant else "",
            "total_price": cart.total_price if cart else 0.0
        }

    items = []
    for item in cart.item_associations:
        items.append({
            "id": item.dish_id,
            "name": item.dish.name,
            "amount": item.amount,
            "price": item.price_at_time,
            "total": item.amount * item.price_at_time
        })

    return {
        "cart_items": items,
        "cart_empty": False,
        "restaurant_name": cart.restaurant.name if cart.restaurant else "",
        "total_price": cart.total_price or 0.0
    }


async def get_cart_item_for_edit(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    """Получает информацию о выбранном блюде для редактирования"""
    cart_id = dialog_manager.dialog_data.get("cart_id")
    dish_id = dialog_manager.dialog_data.get("edit_dish_id")

    cart_item = await CartItemRepository(session).get_cart_item(cart_id, dish_id)
    dish = await DishRepository(session).get_dish_by_id(dish_id)

    if not cart_item or not dish:
        return {
            "dish_name": "Не найдено",
            "current_amount": 0,
            "price": 0,
            "total": 0
        }

    return {
        "dish_name": dish.name,
        "current_amount": cart_item.amount,
        "price": cart_item.price_at_time,
        "total": cart_item.amount * cart_item.price_at_time
    }


async def get_cart_history(
        dialog_manager: DialogManager,
        session: AsyncSession,
        user_row: UserModel,
        **kwargs
) -> Dict[str, Any]:
    """Получает историю заказов пользователя (корзины без is_current=True)"""
    # Получаем все корзины пользователя, кроме текущей
    user_carts = await CartRepository(session).get_user_carts(
        user_id=user_row.id,
    )

    carts_info = []
    for cart in user_carts:
        # Формируем информацию о корзине
        items_text = "\n".join([
            f"  • {item.dish.name} - {item.amount} шт. x {item.price_at_time}₽"
            for item in cart.item_associations[:3]  # Показываем первые 3 позиции
        ])

        if len(cart.item_associations) > 3:
            items_text += f"\n  ... и ещё {len(cart.item_associations) - 3} позиций"

        status_emoji = {
            CartStatus.ACTIVE: "🟢",
            CartStatus.ORDERED: "🟡",
            CartStatus.CANCELLED: "🔴"
        }.get(cart.status, "⚪")

        carts_info.append((
            f"{status_emoji} {cart.restaurant.name}\n"
            f"💰 {cart.total_price or 0:.2f} ₽ | 📅 {cart.created_at.strftime('%d.%m.%Y')}\n",
            cart.id
        ))

    return {
        "carts": carts_info,
        "carts_count": len(carts_info),
        "total_orders": len(user_carts),
        "total_spent": sum(cart.total_price or 0 for cart in user_carts)
    }


async def get_active_orders_for_delivery(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    """Получает активные заявки на доставку за сегодня"""
    today = datetime.today().date()
    active_orders = await OrderRepository(session).get_orders_by_date(
        order_date=today,
        status=OrderStatus.COLLECTING
    )

    orders_info = []
    for order in active_orders:
        # Считаем количество корзин в заказе
        carts_count = len(order.carts) if order.carts else 0

        orders_info.append((
            f"🚚 {order.restaurant.name}\n"
            f"📦 {carts_count} корзин | 💰 {order.total_amount:.2f} ₽\n"
            f"⏰ {order.created_at.strftime('%H:%M')}",
            order.id
        ))

    return {
        "orders": orders_info,
        "orders_count": len(orders_info),
        "today_date": today.strftime("%d.%m.%Y")
    }


async def get_carts_for_order(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    """Получает все корзины в выбранном заказе"""
    order_id = dialog_manager.dialog_data.get("selected_order_id")
    order = await OrderRepository(session).get_order_with_carts(order_id)

    if not order:
        return {
            "order_info": "Заказ не найден",
            "carts": [],
            "carts_count": 0,
            "order_total": 0
        }

    carts_info = []
    for cart in order.carts:
        # Формируем информацию о корзине пользователя
        user = cart.user
        username = user.mention if user else "Без пользователя"

        items_text = "\n".join([
            f"    • {item.dish.name} - {item.amount} шт."
            for item in cart.item_associations
        ])

        carts_info.append((
            f"👤 {username}\n"
            f"📦 Корзина #{cart.id}\n"
            f"💰 {cart.total_price or 0:.2f} ₽\n"
            f"{items_text}",
            cart.id
        ))

    return {
        "order_info": f"Заказ #{order.id} | {order.restaurant.name}",
        "carts": carts_info,
        "carts_count": len(order.carts),
        "order_total": order.total_amount,
        "order_status": order.status.value
    }
