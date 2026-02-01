from enum import Enum


class CartStatus(Enum):
    ACTIVE = "🟡 Не включена в доставку"
    ORDERED = "✅ Включена в доставку"
    CANCELLED = "🔴 Отменена"
