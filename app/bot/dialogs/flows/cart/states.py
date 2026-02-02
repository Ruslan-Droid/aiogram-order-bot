from aiogram.fsm.state import StatesGroup, State


class CartSG(StatesGroup):
    main = State()
    add_comment = State()
    add_to_existing_order = State()
    edit_cart = State()
    edit_cart_item = State()  # Для редактирования количества конкретного блюда
    show_cart_history = State()  # История заказов
    show_carts_for_order = State()  # Для просмотра корзин в конкретном заказе
    show_all_carts = State()  # Все заказы для доставщика
