from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Select, Button

from app.bot.dialogs.flows.cart.states import CartSG
from app.infrastructure.database.query.cart_queries import CartRepository
from app.infrastructure.database.query.order_queries import OrderRepository
from app.infrastructure.database.models.cart import CartStatus


async def on_order_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]
    cart_id = manager.start_data.get("cart_id")

    order_repo = OrderRepository(session)
    cart_repo = CartRepository(session)

    # Привязываем корзину к заказу
    await cart_repo.attach_cart_to_order(
        cart_id=int(cart_id),
        order_id=int(item_id)
    )

    # Создаем новую пустую корзину для пользователя
    cart = await cart_repo.get_cart_by_id(cart_id)
    new_cart = await cart_repo.get_or_create_active_cart(
        user_id=cart.user_id,
        restaurant_id=cart.restaurant_id
    )

    # Обновляем cart_id в dialog_data для новой корзины
    manager.dialog_data["cart_id"] = new_cart.id

    await callback.answer(f"✅ Корзина добавлена к заказу #{item_id}")
    await manager.switch_to(CartSG.main)


async def on_comment_entered(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):
    session = dialog_manager.middleware_data["session"]
    cart_id = dialog_manager.start_data.get("cart_id")

    cart_repo = CartRepository(session)
    await cart_repo.update_cart_notes(cart_id, message.text)

    await message.answer("📝 Комментарий добавлен!")
    await dialog_manager.switch_to(CartSG.main)


async def on_edit_cart_clicked(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    """Переход к редактированию корзины"""
    cart_id = dialog_manager.start_data.get("cart_id")

    # Возвращаемся в меню для редактирования
    await dialog_manager.done()
    from app.bot.dialogs.flows.menu_view.states import MenuViewSG
    await dialog_manager.start(
        MenuViewSG.restaurants,
        data={"cart_id": cart_id}
    )