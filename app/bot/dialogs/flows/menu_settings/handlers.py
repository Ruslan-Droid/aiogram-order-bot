import re

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


def validate_and_split_dish_name_and_price(input_text: str) -> tuple[str, float]:
    if not input_text or len(input_text.strip()) < 3:
        raise ValueError("Введите название и цену")

    parts = input_text.strip().split()

    if len(parts) < 2:
        raise ValueError("Введите и название, и цену")

    # Берем последний элемент как цену
    try:
        price = float(parts[-1].replace(',', '.'))
    except:
        raise ValueError("Цена должна быть числом")

    if price <= 0:
        raise ValueError("Цена должна быть положительной")

    # Все остальное - название
    dish_name = ' '.join(parts[:-1])

    if len(dish_name) < 2:
        raise ValueError("Название слишком короткое")

    return dish_name, price


async def process_success_dish_name_and_price(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        data: tuple[str, float],
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    category_id = dialog_manager.dialog_data.get("category_id")
    dish_name, price = data

    try:
        await DishRepository(session).create_dish(name=dish_name, price=price, category_id=int(category_id))
        await message.answer(f"✅ Блюдо успешно создано: {dish_name} цена {price}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.dishes_menu)


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

    await manager.switch_to(MenuSettingsSG.delete_dish)


async def on_dish_selected_rename(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
) -> None:
    manager.dialog_data["dish_id"] = item_id
    await manager.switch_to(state=MenuSettingsSG.rename_dish_input)


async def process_success_dish_rename(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    dish_id = dialog_manager.dialog_data.get("dish_id")

    try:
        await DishRepository(session).update_dish_name(name=text, dish_id=int(dish_id))
        await message.answer(f"✅ Блюдо успешно переименовано: {text}")
    except Exception as error:
        await message.answer(f"Error: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.rename_dish)


def validate_price(text: str) -> str:
    """Простая валидация, не бросающая исключения"""
    if not text:
        return "ERROR: Введите цену"

    text = text.strip()
    text = text.replace(',', '.')

    # Пробуем преобразовать в float
    try:
        price = float(text)
    except ValueError:
        return "ERROR: Цена должна быть числом (например: 199.99, 200, 150.50)"

    # Проверяем, что цена положительная
    if price <= 0:
        return "ERROR: Цена должна быть больше нуля"

    # Возвращаем отформатированную цену
    return f"{price:.2f}"


async def on_dish_selected_update_price(
        callback: CallbackQuery,
        widget: Select,
        manager: DialogManager,
        item_id: str
) -> None:
    manager.dialog_data["dish_id"] = item_id
    await manager.switch_to(state=MenuSettingsSG.change_dish_price_input)


async def process_success_dish_update_price(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str,
) -> None:
    # Проверяем, не содержит ли текст ошибку
    if text.startswith("ERROR:"):
        # Это ошибка валидации
        error_message = text[6:]  # Убираем "ERROR:"
        await message.answer(f"❌ Ошибка: {error_message}")
        return  # Не переключаем состояние, остаемся в текущем

    # Если все хорошо, обновляем цену
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    dish_id = dialog_manager.dialog_data.get("dish_id")

    try:
        await DishRepository(session).update_dish_price(
            price=float(text),
            dish_id=int(dish_id)
        )
        await message.answer(f"✅ Цена успешно обновлена: {text}")
    except Exception as error:
        await message.answer(f"❌ Ошибка при обновлении: {error}")

    await dialog_manager.switch_to(MenuSettingsSG.change_dish_price)


def parse_dishes_input(text: str) -> list[tuple[str, float]]:
    """Парсит строку с блюдами в формате 'Название:цена, Название:цена'"""
    if not text.strip():
        raise ValueError("Введите хотя бы одно блюдо")

    dishes = []
    items = [item.strip() for item in text.split(',') if item.strip()]

    for item in items:
        if ':' not in item:
            raise ValueError(f"Неверный формат: '{item}'. Используйте 'Название:цена'")

        name, price_str = item.rsplit(':', 1)
        name = name.strip()
        price_str = price_str.strip()

        if not name:
            raise ValueError(f"Укажите название блюда: '{item}'")

        # Проверяем формат цены
        if not re.match(r'^\d+(\.\d{1,2})?$', price_str):
            raise ValueError(f"Неверный формат цены: '{price_str}'. Используйте числа, например: 200 или 500.50")

        try:
            price = float(price_str)
            if price <= 0:
                raise ValueError(f"Цена должна быть больше 0: '{price_str}'")
        except Exception as e:
            raise ValueError(f"Ошибка преобразования цены '{price_str}': {str(e)}")

        dishes.append((name, price))

    return dishes


async def handle_multiple_dishes_added(
        message: Message,
        widget: ManagedTextInput,
        manager: DialogManager,
        dishes_data: list[tuple[str, float]],
        **kwargs
):
    session = manager.middleware_data["session"]
    dish_repo = DishRepository(session)
    # Получаем category_id из состояния или данных диалога
    category_id = manager.dialog_data.get("category_id")

    if not category_id:
        raise ValueError("Не выбрана категория для добавления блюд")

    # Получаем текущий максимальный display_order для категории

    created_dishes = []
    errors = []

    for i, (dish_name, price) in enumerate(dishes_data, start=1):
        try:
            # Проверяем, существует ли уже такое блюдо в категории
            # (в данном коде нет метода для проверки по имени, можно добавить или сделать запрос)

            dish = await dish_repo.create_dish(
                name=dish_name,
                price=float(price),  # Преобразуем Decimal в float для модели
                category_id=category_id,
            )
            created_dishes.append(dish)
        except Exception as e:
            errors.append(f"{dish_name}: {str(e)}")

    if created_dishes:
        success_msg = f"✅ Успешно добавлено {len(created_dishes)} блюд:\n"
        for dish in created_dishes:
            success_msg += f"• {dish.name} - {dish.formatted_price}\n"

        if errors:
            success_msg += f"\n❌ Ошибки ({len(errors)}):\n"
            for error in errors:
                success_msg += f"• {error}\n"

        await message.answer(success_msg)
    else:
        await message.answer("❌ Не удалось добавить ни одного блюда. Проверьте формат ввода.")

    await manager.switch_to(MenuSettingsSG.dishes_menu)


async def handle_dishes_parse_error(
        message: Message,
        widget: ManagedTextInput,
        manager: DialogManager,
        error: ValueError,
        **kwargs
):
    """Обработчик ошибок парсинга блюд"""
    error_msg = "❌ Ошибка формата:\n"

    if "Неверный формат" in str(error):
        error_msg += f"{str(error)}\n\n"
    elif "Укажите название" in str(error):
        error_msg += f"{str(error)}\n\n"
    elif "Неверный формат цены" in str(error):
        error_msg += f"{str(error)}\n\n"
    elif "Цена должна быть больше 0" in str(error):
        error_msg += f"{str(error)}\n\n"
    else:
        error_msg += f"{str(error)}\n\n"

    error_msg += "Правильный формат:\n"
    error_msg += "Название блюда:цена\n"
    error_msg += "Пример: Куриное филе:200, Картошка фри:500.50"

    await message.answer(error_msg)
