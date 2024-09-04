from enum import IntEnum

ChatMemberStatus = IntEnum(
    "ChatMemberStatus",
    ["Unknown", "Creator", "Administrator", "Member", "Restricted", "Left", "Banned"],
    start=0,
)

__all__ = ["ChatMemberStatus"]
