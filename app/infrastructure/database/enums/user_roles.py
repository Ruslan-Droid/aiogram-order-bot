from enum import Enum


class UserRole(str, Enum):
    UNKNOWN = "unknown"
    MEMBER = "member"
    ADMIN = "admin"
    OWNER = "owner"
