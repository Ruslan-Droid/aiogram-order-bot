from typing import Any
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, Window, ShowMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Select, Multiselect
from aiogram_dialog.widgets.text import Const, Format

from app.infrastructure.database.query.restaurant_queries import RestaurantRepository
from app.infrastructure.database.query.category_queries import CategoryRepository
from app.infrastructure.database.query.dish_queries import DishRepository
from .states import MenuSettingsSG


# Обработчики для заведений
async def on_restaurant_selected(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]
    repo = RestaurantRepository(session)

    restaurant = await repo.get_restaurant_by_id(int(item_id))
    if restaurant:
        manager.dialog_data["restaurant_id"] = restaurant.id
        manager.dialog_data["restaurant_name"] = restaurant.name
        await manager.switch_to(MenuSettingsSG.categories_menu)


async def add_restaurant_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text:
        return

    session = manager.middleware_data["session"]
    repo = RestaurantRepository(session)

    try:
        restaurant = await repo.create_restaurant(name=message.text.strip())
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при создании заведения: {e}")


async def delete_restaurant_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text:
        return

    try:
        restaurant_id = int(message.text.strip())
        session = manager.middleware_data["session"]
        repo = RestaurantRepository(session)

        await repo.delete_restaurant(restaurant_id)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при удалении заведения: {e}")


async def rename_restaurant_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text or '|' not in message.text:
        await message.answer("Формат: id|новое_название")
        return

    try:
        parts = message.text.split('|', 1)
        restaurant_id = int(parts[0].strip())
        new_name = parts[1].strip()

        session = manager.middleware_data["session"]
        repo = RestaurantRepository(session)

        await repo.update_restaurant_name(restaurant_id, new_name)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при переименовании заведения: {e}")


# Обработчики для категорий
async def on_category_selected(
        callback: CallbackQuery,
        widget: ManagedMultiSelectAdapter,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]
    repo = CategoryRepository(session)

    category = await repo.get_category_by_id(int(item_id))
    if category:
        manager.dialog_data["category_id"] = category.id
        manager.dialog_data["category_name"] = category.name
        await manager.switch_to(MenuSettingsSG.dishes_menu)


async def add_category_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text:
        return

    restaurant_id = manager.dialog_data.get("restaurant_id")
    if not restaurant_id:
        await message.answer("Не выбрано заведение")
        return

    session = manager.middleware_data["session"]
    repo = CategoryRepository(session)

    try:
        category = await repo.create_category(
            name=message.text.strip(),
            restaurant_id=restaurant_id
        )
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при создании категории: {e}")


async def delete_category_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text:
        return

    try:
        category_id = int(message.text.strip())
        session = manager.middleware_data["session"]
        repo = CategoryRepository(session)

        await repo.delete_category(category_id)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при удалении категории: {e}")


async def rename_category_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text or '|' not in message.text:
        await message.answer("Формат: id|новое_название")
        return

    try:
        parts = message.text.split('|', 1)
        category_id = int(parts[0].strip())
        new_name = parts[1].strip()

        # Здесь нужно добавить метод update_category_name в репозиторий
        # Показываю логику, добавьте метод в CategoryRepository
        session = manager.middleware_data["session"]
        # repo.update_category_name(category_id, new_name)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при переименовании категории: {e}")


# Обработчики для блюд
async def add_dish_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text or '|' not in message.text:
        await message.answer("Формат: название|цена")
        return

    category_id = manager.dialog_data.get("category_id")
    if not category_id:
        await message.answer("Не выбрана категория")
        return

    try:
        parts = message.text.split('|', 1)
        name = parts[0].strip()
        price = float(parts[1].strip())

        session = manager.middleware_data["session"]
        repo = DishRepository(session)

        dish = await repo.create_dish(
            name=name,
            price=price,
            category_id=category_id
        )
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при создании блюда: {e}")


async def delete_dish_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text:
        return

    try:
        dish_id = int(message.text.strip())
        session = manager.middleware_data["session"]
        repo = DishRepository(session)

        await repo.delete_dish(dish_id)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при удалении блюда: {e}")


async def rename_dish_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text or '|' not in message.text:
        await message.answer("Формат: id|новое_название")
        return

    try:
        parts = message.text.split('|', 1)
        dish_id = int(parts[0].strip())
        new_name = parts[1].strip()

        # Здесь нужно добавить метод update_dish_name в репозиторий
        session = manager.middleware_data["session"]
        # repo.update_dish_name(dish_id, new_name)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при переименовании блюда: {e}")


async def change_dish_price_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text or '|' not in message.text:
        await message.answer("Формат: id|новая_цена")
        return

    try:
        parts = message.text.split('|', 1)
        dish_id = int(parts[0].strip())
        new_price = float(parts[1].strip())

        session = manager.middleware_data["session"]
        repo = DishRepository(session)

        await repo.update_dish_price(dish_id, new_price)
        manager.show_mode = ShowMode.SEND
        await manager.back()
    except Exception as e:
        await message.answer(f"Ошибка при изменении цены: {e}")


async def add_multiple_dishes_handler(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager
):
    if not message.text:
        return

    category_id = manager.dialog_data.get("category_id")
    if not category_id:
        await message.answer("Не выбрана категория")
        return

    session = manager.middleware_data["session"]
    repo = DishRepository(session)

    lines = message.text.strip().split('\n')
    created_count = 0

    for line in lines:
        if '|' in line:
            try:
                name, price_str = line.split('|', 1)
                name = name.strip()
                price = float(price_str.strip())

                await repo.create_dish(
                    name=name,
                    price=price,
                    category_id=category_id
                )
                created_count += 1
            except:
                continue

    await message.answer(f"Добавлено {created_count} блюд из {len(lines)} строк")
    manager.show_mode = ShowMode.SEND
    await manager.back()


# Навигационные обработчики
async def go_to_restaurant_settings(
        callback: CallbackQuery,
        button: Button,
        manager: DialogManager
) -> None:
    await manager.switch_to(MenuSettingsSG.restaurant_menu)


async def go_to_category_settings(
        callback: CallbackQuery,
        button: Button,
        manager: DialogManager
) -> None:
    await manager.switch_to(MenuSettingsSG.select_restaurant_for_category)


async def go_to_dish_settings(
        callback: CallbackQuery,
        button: Button,
        manager: DialogManager
) -> None:
    await manager.switch_to(MenuSettingsSG.select_category_for_dish)


async def go_back(
        callback: CallbackQuery,
        button: Button,
        manager: DialogManager
) -> None:
    await manager.back()
