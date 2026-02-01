from typing import Dict, Any

from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel, CategoryModel, RestaurantModel, DishModel
from app.infrastructure.database.query.category_queries import CategoryRepository
from app.infrastructure.database.query.dish_queries import DishRepository
from app.infrastructure.database.query.restaurant_queries import RestaurantRepository


async def get_restaurants_for_menu(
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


async def get_categories_for_menu(
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


async def get_dishes_for_menu(
        dialog_manager: DialogManager,
        session: AsyncSession,
        user_row: UserModel,
        **kwargs
) -> Dict[str, Any]:
    category_id = dialog_manager.dialog_data.get("category_id")
    category_name = dialog_manager.dialog_data.get("category_name")

    dishes: list[DishModel] = await DishRepository(session).get_dishes_by_category(category_id)

    return {
        "dishes": [
            (f"{dish.name} - {dish.formatted_price}", dish.id) for dish in dishes
        ],
        "category_name": category_name,
        "count": len(dishes),
    }
