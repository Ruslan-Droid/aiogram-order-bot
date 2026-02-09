from aiogram import Bot
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import DeliveryOrderModel
from app.infrastructure.database.query.order_queries import OrderRepository


async def send_carts_summary_message(
        bot: Bot,
        chat_id: int,
        order: DeliveryOrderModel,
) -> None:
    """Отправить сводное сообщение со всеми корзинами"""
    try:
        # Заголовок сообщения
        header = (
            f"📋 <b>ЗАКАЗ #{order.id}</b>\n"
            f"📍 Ресторан: {order.restaurant.name}\n"
            f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"👥 Участников: {len(order.carts)}\n"
            f"💰 <b>Общая сумма: {order.total_amount:.2f} ₽</b>\n"
            f"────────────────────\n\n"
        )

        current_text = header
        message_parts = []

        # Формируем информацию по каждому пользователю
        user_carts = {}
        for cart in order.carts:
            if cart.user_id not in user_carts:
                user_carts[cart.user_id] = []
            user_carts[cart.user_id].append(cart)

        # Для каждого пользователя формируем блок
        for user_id, carts in user_carts.items():
            user = carts[0].user

            # Формируем информацию о пользователе
            username = user.mention if user else "Без пользователя"
            user_total = sum(cart.total_price or 0 for cart in carts)

            user_block = (
                f"👤 <b>{username}</b>\n"
            )

            # Добавляем информацию о каждой корзине пользователя
            for cart in carts:
                if cart.notes:
                    user_block += f"⚠️ <b>{cart.notes}</b>\n"

                user_block += f"🍽 Позиции:\n"
                for item in cart.item_associations:
                    item_total = item.amount * item.price_at_time
                    user_block += (
                        f"{item.dish.name} - "
                        f"{item.amount} шт. × {item.price_at_time:.2f} ₽ = "
                        f"<b>{item_total:.2f} ₽</b>\n"
                    )

            user_block += f"\n💰 <b>Итого: {user_total:.2f} ₽</b>\n"
            user_block += "────────────────────\n"

            # Проверяем длину сообщения
            if len(current_text + user_block) > 4000:
                message_parts.append(current_text)
                current_text = user_block
            else:
                current_text += user_block

        # Добавляем последнюю часть
        if current_text:
            message_parts.append(current_text)

        # Отправляем все части сообщения
        for i, text in enumerate(message_parts):
            # Клавиатура только для последнего сообщения
            reply_markup = None
            if i == len(message_parts) - 1:
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text="📊 Показать сводный список товаров",
                    callback_data=f"order_summary:{order.id}"
                ))
                reply_markup = builder.as_markup()

            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

    except Exception:
        raise


async def send_grouped_items_message(
        callback: CallbackQuery,
        order_id: int,
        session: AsyncSession
) -> None:
    """Отправить сообщение с группировкой товаров по категориям"""
    try:
        order_repo = OrderRepository(session)
        order = await order_repo.get_order_with_carts(order_id)

        if not order:
            await callback.answer("Заказ не найден", show_alert=True)
            return

        # Собираем все товары из всех корзин
        all_items = []
        for cart in order.carts:
            for item in cart.item_associations:
                all_items.append({
                    'dish_id': item.dish.id,
                    'dish_name': item.dish.name,
                    'amount': item.amount,
                    'price': item.price_at_time,
                    'category_id': item.dish.category_id,
                    'category_name': item.dish.category.name if item.dish.category else "Без категории",
                    'category_order': item.dish.category.display_order if item.dish.category else 999
                })

        # Группируем товары по названию
        grouped_items = {}
        for item in all_items:
            key = item['dish_id']
            if key not in grouped_items:
                grouped_items[key] = {
                    'name': item['dish_name'],
                    'total_amount': 0,
                    'category_id': item['category_id'],
                    'category_name': item['category_name'],
                    'category_order': item['category_order'],
                    'price': item['price'],
                    'total_price': 0
                }
            grouped_items[key]['total_amount'] += item['amount']

        # Рассчитываем общую стоимость для каждого товара
        for key, item_data in grouped_items.items():
            item_data['total_price'] = item_data['total_amount'] * item_data['price']

        # Группируем товары по категориям
        categories = {}
        for item_data in grouped_items.values():
            cat_id = item_data['category_id']
            if cat_id not in categories:
                categories[cat_id] = {
                    'name': item_data['category_name'],
                    'order': item_data['category_order'],
                    'items': [],
                    'total_amount': 0,
                    'total_price': 0
                }

            categories[cat_id]['items'].append(item_data)
            categories[cat_id]['total_amount'] += item_data['total_amount']
            categories[cat_id]['total_price'] += item_data['total_price']

        # Сортируем категории по display_order
        sorted_categories = sorted(categories.values(), key=lambda x: (x['order'], x['name']))

        # Формируем сообщение
        header = (
            f"📊 <b>СВОДНЫЙ СПИСОК ТОВАРОВ</b>\n"
            f"Заказ #{order.id} | {order.restaurant.name}\n"
            f"────────────────────\n\n"
        )

        message_text = header
        total_all_items = 0
        total_all_price = 0

        for category in sorted_categories:
            # Сортируем товары в категории по названию
            sorted_items = sorted(category['items'], key=lambda x: x['name'])

            category_text = (
                f"📁 <b>{category['name']}</b>\n"
                f"Общее количество: {category['total_amount']} шт.\n"
                f"На сумму: <b>{category['total_price']:.2f} ₽</b>\n\n"
            )

            for item in sorted_items:
                category_text += (
                    f"  • {item['name']} - "
                    f"<b>{item['total_amount']} шт.</b> "
                    f"({item['price']:.2f} ₽/шт.)\n"
                )

            category_text += "────────────────────\n\n"

            # Проверяем длину сообщения
            if len(message_text + category_text) > 4000:
                await callback.message.answer(
                    text=message_text,
                    parse_mode="HTML"
                )
                message_text = category_text
            else:
                message_text += category_text

            total_all_items += category['total_amount']
            total_all_price += category['total_price']

        # Добавляем итоги
        summary = (
            f"📈 <b>ИТОГИ ПО ЗАКАЗУ</b>\n"
            f"Общее количество товаров: <b>{total_all_items} шт.</b>\n"
            f"Общая стоимость: <b>{total_all_price:.2f} ₽</b>\n"
        )

        if len(message_text + summary) > 4000:
            await callback.message.answer(
                text=message_text,
                parse_mode="HTML"
            )
            message_text = summary
        else:
            message_text += summary

        # Отправляем финальное сообщение
        await callback.message.answer(
            text=message_text,
            parse_mode="HTML"
        )

        await callback.answer()

    except Exception as e:
        await callback.answer("Ошибка при формировании сводного списка", show_alert=True)
