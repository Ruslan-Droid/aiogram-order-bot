from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import MessageInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Select

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.query.restaurant_queries import RestaurantRepository
from app.infrastructure.database.query.category_queries import CategoryRepository
from app.infrastructure.database.query.dish_queries import DishRepository
from .states import MenuSettingsSG


# 🏢 Обработчики для заведений
# ✅
def validate_name(text: str) -> str:
    if not text:
        raise TypeError("Введите текст")

    return text.strip()


# ✅
async def process_success_restaurant_name(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")

    try:
        await RestaurantRepository(session).create_restaurant(name=text)
        await message.answer(f"✅ Заведение успешно создано: {text}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.restaurant_menu)


# ✅
async def process_error_name(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: Exception
) -> None:
    error_message = str(error)

    await message.answer(f"❌ Ошибка: {error_message}")


# ✅
async def on_restaurant_selected_delete(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session: AsyncSession = manager.middleware_data["session"]
    repo = RestaurantRepository(session)

    try:
        await repo.update_restaurant_status(int(item_id), is_active=False)
        await callback.message.answer("✅ Заведение успешно удалено")
    except Exception as error:
        await callback.message.answer(f"Error: {str(error)}")

    await manager.switch_to(MenuSettingsSG.delete_restaurant)


# ✅
async def on_restaurant_selected_recover(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session: AsyncSession = manager.middleware_data["session"]
    repo = RestaurantRepository(session)

    try:
        await repo.update_restaurant_status(int(item_id), is_active=True)
        await callback.message.answer("✅ Заведение успешно удалено")
    except Exception as error:
        await callback.message.answer(f"Error: {str(error)}")

    await manager.switch_to(MenuSettingsSG.delete_restaurant)


# ✅
async def on_restaurant_selected_rename(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
) -> None:
    manager.dialog_data["restaurant_id"] = item_id
    await manager.switch_to(state=MenuSettingsSG.rename_restaurant_input)


# ✅
async def process_success_restaurant_rename(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    restaurant_id = dialog_manager.dialog_data.get("restaurant_id")

    try:
        await RestaurantRepository(session).update_restaurant_name(name=text.strip(), restaurant_id=int(restaurant_id))
        await message.answer(f"✅ Заведение переименовано: {text}")

    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.rename_restaurant)


# Обработчики для категорий
# ✅
async def on_restaurant_selected_for_categories(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]

    restaurant = await RestaurantRepository(session).get_restaurant_by_id(int(item_id))
    if restaurant:
        manager.dialog_data["restaurant_id"] = restaurant.id
        manager.dialog_data["restaurant_name"] = restaurant.name
    await manager.switch_to(state=MenuSettingsSG.categories_menu)


async def process_success_category_name(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    restaurant_id = dialog_manager.dialog_data.get("restaurant_id")

    try:
        await CategoryRepository(session).create_category(name=text, restaurant_id=int(restaurant_id))
        await message.answer(f"✅ Категория успешно создано: {text}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.categories_menu)


async def on_category_selected_rename(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
) -> None:
    manager.dialog_data["category_id"] = item_id
    await manager.switch_to(state=MenuSettingsSG.rename_category_input)


async def process_success_category_rename(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    category_id = dialog_manager.dialog_data.get("category_id")

    try:
        await CategoryRepository(session).update_category_name(name=text, category_id=int(category_id))
        await message.answer(f"✅ Категория успешно переименована: {text}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.rename_category)


async def on_category_selected_delete(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session: AsyncSession = manager.middleware_data["session"]

    try:
        await CategoryRepository(session).update_category_status(int(item_id), is_active=False)
        await callback.message.answer("✅ Категория успешно удалена")
    except Exception as error:
        await callback.message.answer(f"Error: {str(error)}")

    await manager.switch_to(MenuSettingsSG.delete_category)


# Обработчики для блюд
async def on_restaurant_selected_for_dishes(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session = manager.middleware_data["session"]

    restaurant = await RestaurantRepository(session).get_restaurant_by_id(int(item_id))
    if restaurant:
        manager.dialog_data["restaurant_id"] = restaurant.id
        manager.dialog_data["restaurant_name"] = restaurant.name
    await manager.switch_to(state=MenuSettingsSG.select_category_for_dish)


async def on_category_selected_for_dishes(
        callback: CallbackQuery,
        widget: Select,
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


async def process_success_dish_name(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    category_id = dialog_manager.dialog_data.get("category_id")

    try:
        await DishRepository(session).create_dish(name=text, category_id=int(category_id), price=price)
        await message.answer(f"✅ Блюдо успешно создано: {text}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.categories_menu)


async def on_category_selected_rename(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
) -> None:
    manager.dialog_data["category_id"] = item_id
    await manager.switch_to(state=MenuSettingsSG.rename_category_input)


async def process_success_category_rename(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    category_id = dialog_manager.dialog_data.get("category_id")

    try:
        await CategoryRepository(session).update_category_name(name=text, category_id=int(category_id))
        await message.answer(f"✅ Категория успешно переименована: {text}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.rename_category)


async def on_dish_selected_delete(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
):
    session: AsyncSession = manager.middleware_data["session"]

    try:
        await DishRepository(session).update_dish_status(int(item_id), status=False)
        await callback.message.answer("✅ Блюдо успешно удалено")
    except Exception as error:
        await callback.message.answer(f"Error: {str(error)}")

    await manager.switch_to(MenuSettingsSG.delete_category)


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
