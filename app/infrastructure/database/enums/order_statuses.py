from enum import Enum


class OrderStatus(str, Enum):
    COLLECTING = "Собирается"
    COLLECTED = "Собран"
    DELIVERED = "Доставлен"
    CANCELLED = "Отменен"
