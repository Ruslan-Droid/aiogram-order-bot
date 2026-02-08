from typing import Any, Dict
from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import DishModel, CategoryModel, RestaurantModel
from app.infrastructure.database.query.restaurant_queries import RestaurantRepository
from app.infrastructure.database.query.category_queries import CategoryRepository
from app.infrastructure.database.query.dish_queries import DishRepository


async def get_restaurants(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    restaurants: list[RestaurantModel] = await RestaurantRepository(session).get_all_active_restaurants()

    return {
        "restaurants": [
            (restaurant.name, restaurant.id) for restaurant in restaurants
        ],
        "count": len(restaurants)
    }


async def get_deleted_restaurants(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    restaurants: list[RestaurantModel] = await RestaurantRepository(session).get_all_disabled_restaurants()

    return {
        "restaurants": [
            (restaurant.name, restaurant.id) for restaurant in restaurants
        ],
        "count": len(restaurants)
    }


async def get_categories_for_restaurant(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    restaurant_id = dialog_manager.dialog_data.get("restaurant_id")
    if not restaurant_id:
        return {"categories": [], "count": 0}

    categories: list[CategoryModel] = await CategoryRepository(session).get_categories_by_restaurant(int(restaurant_id))

    return {
        "categories": [
            (category.name, category.id) for category in categories
        ],
        "count": len(categories),
        "restaurant_name": dialog_manager.dialog_data.get("restaurant_name", "")
    }


async def get_dishes_for_category(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> Dict[str, Any]:
    category_id = dialog_manager.dialog_data.get("category_id")
    if not category_id:
        return {"dishes": [], "count": 0}

    dishes: list[DishModel] = await DishRepository(session).get_dishes_by_category(category_id)

    return {
        "dishes": [
            (f"{dish.name} - {dish.formatted_price}", dish.id) for dish in dishes
        ],
        "count": len(dishes),
        "category_name": dialog_manager.dialog_data.get("category_name", "")
    }


async def get_selected_restaurant(
        dialog_manager: DialogManager,
        **kwargs
) -> Dict[str, Any]:
    return {
        "restaurant_name": dialog_manager.dialog_data.get("restaurant_name", ""),
        "restaurant_id": dialog_manager.dialog_data.get("restaurant_id", "")
    }


async def get_selected_category(
        dialog_manager: DialogManager,
        **kwargs
) -> Dict[str, Any]:
    return {
        "category_name": dialog_manager.dialog_data.get("category_name", ""),
        "category_id": dialog_manager.dialog_data.get("category_id", ""),
        "restaurant_name": dialog_manager.dialog_data.get("restaurant_name", "")
    }


async def get_selected_dish(
        dialog_manager: DialogManager,
        **kwargs
) -> Dict[str, Any]:
    return {
        "dish_name": dialog_manager.dialog_data.get("dish_name", ""),
        "dish_price": dialog_manager.dialog_data.get("dish_price", ""),
        "category_name": dialog_manager.dialog_data.get("category_name", "")
    }
