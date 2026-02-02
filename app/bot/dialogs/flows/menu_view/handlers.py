from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Select, Button
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.dialogs.flows.cart.states import CartSG
from app.bot.dialogs.flows.menu_view.states import MenuViewSG
from app.bot.dialogs.widgets.MultiSelectCounter import MultiSelectCounter
from app.infrastructure.database.models import UserModel, RestaurantModel, CategoryModel, CartModel
from app.infrastructure.database.query.cart_queries import CartRepository, CartItemRepository
from app.infrastructure.database.query.category_queries import CategoryRepository
from app.infrastructure.database.query.dish_queries import DishRepository
from app.infrastructure.database.query.restaurant_queries import RestaurantRepository


async def on_restaurant_selected_for_menu_view(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]

    restaurant: RestaurantModel = await RestaurantRepository(session).get_restaurant_by_id(int(item_id))

    if restaurant:
        manager.dialog_data["restaurant_id"] = restaurant.id
        manager.dialog_data["restaurant_name"] = restaurant.name
    await manager.switch_to(state=MenuViewSG.categories)


async def on_category_selected_for_menu_view(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]

    category: CategoryModel = await CategoryRepository(session).get_category_by_id(int(item_id))

    if category:
        manager.dialog_data["category_id"] = category.id
        manager.dialog_data["category_name"] = category.name
    await manager.switch_to(MenuViewSG.dishes)


async def on_add_to_cart_clicked(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    session: AsyncSession = dialog_manager.middleware_data["session"]
    user: UserModel = dialog_manager.middleware_data["user_row"]
    restaurant_id = dialog_manager.dialog_data["restaurant_id"]

    multi_counter_widget: MultiSelectCounter = dialog_manager.find("multi_counter")
    managed_multi_counter = multi_counter_widget.managed(dialog_manager)

    cart_repo = CartRepository(session)

    # Получаем все счетчики
    counters_data = managed_multi_counter.get_counters_data()
    if not counters_data:
        await callback.answer("Выберите что нибудь для добавления в корзину!")
        return

    # Создаем или получаем корзину
    cart = await cart_repo.get_or_create_active_cart(
        user_id=user.id,
        restaurant_id=restaurant_id
    )

    added_items_count = 0
    for dish_id, amount in counters_data.items():
        if amount > 0:
            dish_id = int(dish_id)
            dish = await DishRepository(session).get_dish_by_id(dish_id)

            if dish:
                await CartItemRepository(session).add_or_update_cart_item(
                    cart_id=cart.id,
                    dish_id=dish_id,
                    amount=int(amount),
                    price_at_time=dish.price
                )
                added_items_count += amount

    await cart_repo.update_cart_total_price(cart.id)
    await callback.answer(f"Добавлено {added_items_count} позиций в корзину!", show_alert=True)


async def go_to_cart_clicked(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.done()
    await dialog_manager.start(CartSG.main)
