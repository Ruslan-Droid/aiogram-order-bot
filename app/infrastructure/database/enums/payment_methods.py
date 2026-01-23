from enum import Enum


class PaymentMethod(str, Enum):
    SBER = "Сбер"
    TINKOFF = "Тинькофф"
    ALFA = "Альфа"
    CASH = "Наличные"
    OTHER = "Другой"
