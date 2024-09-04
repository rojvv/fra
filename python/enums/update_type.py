from enum import IntEnum

UpdateType = IntEnum(
    "UpdateType",
    [
        "Unknown",
        "Message",
        "MessageEdited",
        "MessagesDeleted",
        "CallbackQuery",
        "ChatBoost",
        "ChatBoostRemoved",
        "InlineQuery",
        "InlineResultChosen",
        "JoinRequest",
        "ChatMember",
        "ChatMemberMy",
        "MessageReactionCount",
        "MessageReactions",
    ],
    start=0,
)

__all__ = ["UpdateType"]
