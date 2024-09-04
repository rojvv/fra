from enum import IntEnum

ChatType = IntEnum(
    "ChatType",
    ["Unknown", "User", "Channel", "Group", "Supergroup", "Forum"],
    start=0,
)

__all__ = ["ChatType"]
