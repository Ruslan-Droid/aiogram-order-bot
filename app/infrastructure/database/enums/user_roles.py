from enum import Enum


class UserRole(str, Enum):
    UNKNOWN = "unknown"
    BANNED = "ban"
    MEMBER = "member"
    DELIVERY = "delivery"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
