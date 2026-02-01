from .settings.dialogs import settings_language_dialog
from .main_menu.dialogs import main_menu_dialog
from .delivery_requests.dialogs import delivery_dialog
from .roles_management.dialogs import admin_roles_dialog
from .menu_settings.dialogs import menu_settings_dialog
from .cart.dialogs import cart_dialog
from .menu_view.dialogs import menu_view_dialog

__all__ = ["dialogs"]

dialogs = [
    settings_language_dialog,
    main_menu_dialog,
    menu_view_dialog,
    delivery_dialog,
    cart_dialog,
    admin_roles_dialog,
    menu_settings_dialog
]
