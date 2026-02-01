from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Column, Group, Start
from aiogram_dialog.widgets.text import Const

from app.bot.dialogs.flows.main_menu.getters import get_user_role
from app.bot.dialogs.flows.main_menu.states import MainMenuSG
from app.bot.dialogs.flows.menu_view.states import MenuViewSG
from app.bot.dialogs.flows.delivery_requests.states import DeliverySG
from app.bot.dialogs.flows.cart.states import CartSG
from app.bot.dialogs.flows.roles_management.states import AdminPanelSG
from app.bot.dialogs.flows.menu_settings.states import MenuSettingsSG

from app.bot.dialogs.utils.roles_utils import UserRole, role_required

# Main menu
main_menu_dialog = Dialog(
    Window(
        Const("🏠 Главное меню:"),
        Group(
            Column(
                # 📋 Меню (Все пользователи)
                Start(
                    Const("📋 Меню"),
                    id="view_menu",
                    state=MenuViewSG.restaurants
                ),
                Start(
                    Const("🛒 Корзина"),
                    id="view_cart",
                    state=CartSG.main
                ),
                # 🚚 Заявки на доставку (Выездник, Админ)
                Start(
                    Const("🚚 Заявки на доставку"),
                    id="delivery_requests",
                    state=DeliverySG.main,
                    when=role_required(
                        [UserRole.DELIVERY, UserRole.ADMIN, UserRole.SUPER_ADMIN]
                    )
                ),
                # ⚙️ Настроить права пользователей (Админ)
                Start(
                    Const("⚙️ Настроить права пользователей"),
                    id="manage_roles",
                    state=AdminPanelSG.pending_users,
                    when=role_required(
                        [UserRole.ADMIN, UserRole.SUPER_ADMIN]
                    )
                ),
                # 🍽️ Настроить меню (Админ)
                Start(
                    Const("🍽️ Настроить меню"),
                    id="menu_settings",
                    state=MenuSettingsSG.main,
                    when=role_required(
                        [UserRole.ADMIN, UserRole.SUPER_ADMIN]
                    )
                ),
            )
        ),
        state=MainMenuSG.menu,
        getter=get_user_role,
    )
)
