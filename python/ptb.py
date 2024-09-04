import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
import httpx
import asyncio
from telegram import (
    Update,
    User,
    Chat,
    MessageOriginChannel,
    MessageOriginChat,
    MessageOriginHiddenUser,
    MessageOriginUser,
    ChatMember,
)
from telegram.ext import CallbackContext, TypeHandler
from python import Entry, UpdateType, ChatType, MessageType, ChatMemberStatus


logger = logging.getLogger("Analytics")


class Analytics(TypeHandler):
    _timeout: timedelta
    _endpoint: str
    _threshold: int
    _entries: list[Entry]
    _client: httpx.AsyncClient
    _loop: asyncio.AbstractEventLoop
    _timeout_loop_task: asyncio.Task

    def __init__(
        self,
        endpoint: str,
        *,
        timeout: timedelta = 10,
        threshold: int = 10_000,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        super().__init__(Update, self._callback, False)
        self._entries = []
        self._timeout = timeout
        self._endpoint = endpoint
        self._threshold = threshold
        self._client = httpx.AsyncClient()
        self._loop = loop or asyncio.get_event_loop()
        self._timeout_loop_task = self._loop.create_task(self._timeout_loop())

    def destroy(self) -> None:
        self._timeout_loop_task.cancel()

    async def _timeout_loop(self) -> None:
        while True:
            await self._dispatch()
            await asyncio.sleep(self._timeout)

    async def _callback(self, update: Update, context: CallbackContext) -> None:
        entry = construct_entry(update, context)
        if entry is not None:
            self._entries.append(entry)
            if len(self._entries) >= self._threshold:
                await self._dispatch()

    _dispatching = False

    async def _dispatch(self) -> None:
        if self._dispatching or not len(self._entries):
            return
        self._dispatching = True
        try:
            length = len(self._entries)
            response = await self._client.post(self._endpoint, json=self._entries)
            if response.status_code != 200:
                logger.error(
                    "Analytics server returned response with status code %s",
                    response.status_code,
                )
            else:
                self._entries = self._entries[length:]
        except httpx.HTTPError:
            logger.error("Error communicating with analytics server", exc_info=True)
        finally:
            self._dispatching = False


def construct_entry(update: Update, context: CallbackContext) -> Entry | None:
    # shortcut shortcuts
    usr = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat

    # conversion
    update_type_ = UpdateType.Unknown

    if (update.message or update.channel_post or update.business_message) is not None:
        update_type_ = UpdateType.Message
    elif (
        update.edited_message
        or update.edited_channel_post
        or update.edited_business_message
    ) is not None:
        update_type_ = UpdateType.MessageEdited
    elif update.deleted_business_messages is not None:
        update_type_ = UpdateType.MessagesDeleted
    elif update.callback_query is not None:
        update_type_ = UpdateType.CallbackQuery
    elif update.chat_boost is not None:
        update_type_ = UpdateType.ChatBoost
    elif update.removed_chat_boost is not None:
        update_type_ = UpdateType.ChatBoostRemoved
    elif update.inline_query is not None:
        update_type_ = UpdateType.InlineQuery
    elif update.chosen_inline_result is not None:
        update_type_ = UpdateType.InlineResultChosen
    elif update.chat_join_request is not None:
        update_type_ = UpdateType.JoinRequest
    elif update.chat_member is not None:
        update_type_ = UpdateType.ChatMember
    elif update.my_chat_member is not None:
        update_type_ = UpdateType.ChatMemberMy
    elif update.message_reaction_count is not None:
        update_type_ = UpdateType.MessageReactionCount
    elif update.message_reaction is not None:
        update_type_ = UpdateType.MessageReactions

    if update_type_ == UpdateType.Unknown:
        return None

    from_type_ = ChatType.Unknown
    if usr is not None or isinstance(update.effective_sender, User):
        from_type_ = ChatType.User
    else:
        chat_ = (
            update.effective_sender
            if isinstance(update.effective_sender, Chat)
            else chat
        )
        if chat_ is not None:
            if chat_.is_forum:
                from_type_ = ChatType.Forum
            elif chat_.type == "supergroup":
                from_type_ = ChatType.Supergroup
            elif chat_.type == "channel":
                from_type_ = ChatType.Channel
            elif chat_.type == "group":
                from_type_ = ChatType.Group
    if from_type_ == ChatType.Unknown:
        return None

    chat_type_ = ChatType.Unknown
    if chat is not None:
        chat_ = chat
        if chat_ is not None:
            if chat_.is_forum:
                from_type_ = ChatType.Forum
            elif chat_.type == "supergroup":
                from_type_ = ChatType.Supergroup
            elif chat_.type == "channel":
                from_type_ = ChatType.Channel
            elif chat_.type == "group":
                from_type_ = ChatType.Group

    message_type_ = MessageType.Unsupported
    if msg is not None:
        if msg.text is not None and msg.text:
            message_type_ = MessageType.Text
        elif msg.link_preview_options is not None:
            message_type_ = MessageType.Link
        elif msg.photo is not None:
            message_type_ = MessageType.Photo
        elif msg.document is not None:
            message_type_ = MessageType.Document
        elif msg.video is not None:
            message_type_ = MessageType.Video
        elif msg.sticker is not None:
            message_type_ = MessageType.Sticker
        elif msg.animation is not None:
            message_type_ = MessageType.Animation
        elif msg.voice is not None:
            message_type_ = MessageType.Voice
        elif msg.audio is not None:
            message_type_ = MessageType.Audio
        elif msg.dice is not None:
            message_type_ = MessageType.Dice
        elif msg.video_note is not None:
            message_type_ = MessageType.VideoNote
        elif msg.contact is not None:
            message_type_ = MessageType.Contact
        elif msg.game is not None:
            message_type_ = MessageType.Game
        elif msg.poll is not None:
            message_type_ = MessageType.Poll
        elif msg.invoice is not None:
            message_type_ = MessageType.Invoice
        elif msg.venue is not None:
            message_type_ = MessageType.Venue
        elif msg.location is not None:
            message_type_ = MessageType.Location
        elif msg.new_chat_members is not None:
            message_type_ = MessageType.NewChatMembers
        elif msg.left_chat_member is not None:
            message_type_ = MessageType.LeftChatMember
        elif msg.new_chat_title is not None:
            message_type_ = MessageType.NewChatTitle
        elif msg.new_chat_photo is not None:
            message_type_ = MessageType.NewChatPhoto
        elif msg.deleted_chat_photo is not None:
            message_type_ = MessageType.DeletedChatPhoto
        elif msg.group_created is not None:
            message_type_ = MessageType.GroupCreated
        elif msg.supergroup_created is not None:
            message_type_ = MessageType.SupergroupCreated
        elif msg.channel_created is not None:
            message_type_ = MessageType.ChannelCreated
        elif msg.message_auto_delete_timer_changed is not None:
            message_type_ = MessageType.AutoDeleteTimerChanged
        elif msg.migrate_to_chat_id is not None:
            message_type_ = MessageType.ChatMigratedTo
        elif msg.migrate_from_chat_id is not None:
            message_type_ = MessageType.ChatMigratedFrom
        elif msg.pinned_message is not None:
            message_type_ = MessageType.PinnedMessage
        elif msg.user_shared is not None:
            message_type_ = MessageType.UserShared
        elif msg.write_access_allowed is not None:
            message_type_ = MessageType.WriteAccessAllowed
        elif msg.forum_topic_created is not None:
            message_type_ = MessageType.ForumTopicCreated
        elif msg.forum_topic_edited is not None:
            message_type_ = MessageType.ForumTopicEdited
        elif msg.forum_topic_closed is not None:
            message_type_ = MessageType.ForumTopicClosed
        elif msg.forum_topic_reopened is not None:
            message_type_ = MessageType.ForumTopicReopened
        elif msg.video_chat_scheduled is not None:
            message_type_ = MessageType.VideoChatScheduled
        elif msg.video_chat_started is not None:
            message_type_ = MessageType.VideoChatStarted
        elif msg.video_chat_ended is not None:
            message_type_ = MessageType.VideoChatEnded
        elif msg.giveaway is not None:
            message_type_ = MessageType.Giveaway
        elif msg.successful_payment is not None:
            message_type_ = MessageType.SuccessfulPayment
        elif msg.refunded_payment is not None:
            message_type_ = MessageType.RefundedPayment

    forward_from_ = 0
    if msg is not None and msg.forward_origin is not None:
        fwd = msg.forward_origin
        if isinstance(fwd, MessageOriginUser):
            forward_from_ = fwd.sender_user.id
        elif isinstance(fwd, MessageOriginChannel):
            forward_from_ = fwd.chat.id
        elif isinstance(fwd, MessageOriginChat):
            forward_from_ = fwd.sender_chat.id

    forward_name_ = ""
    if msg is not None and msg.forward_origin is not None:
        fwd = msg.forward_origin
        if isinstance(fwd, MessageOriginUser):
            forward_name_ = fwd.sender_user.first_name
            if fwd.sender_user.last_name:
                forward_name_ += " "
                forward_name_ += fwd.sender_user.last_name
                forward_name_ = forward_name_.strip()
        elif isinstance(fwd, MessageOriginChannel):
            forward_name_ = fwd.chat.title or ""
        elif isinstance(fwd, MessageOriginChat):
            forward_name_ = fwd.sender_chat.title or ""
        elif isinstance(fwd, MessageOriginHiddenUser):
            forward_name_ = fwd.sender_user_name

    timestamp = to_iso_string(datetime.now())
    type_ = update_type_
    to = context.bot.id
    from_ = (
        usr.id
        if usr is not None
        else (
            update.effective_sender.id
            if update.effective_sender is not None
            else chat.id if chat is not None else None
        )
    )
    if from_ is None:
        return None

    from_bot = usr.is_bot if usr is not None else False
    from_firstname = (usr.first_name or "") if usr is not None else ""
    from_lastname = (usr.last_name or "") if usr is not None else ""
    from_username = (usr.username or "") if usr is not None else ""
    from_languagecode = (usr.language_code or "") if usr is not None else ""
    from_premium = (usr.is_premium or False) if usr is not None else False
    from_type = from_type_
    from_title = (
        (update.effective_sender.title or "")
        if isinstance(update.effective_sender, Chat)
        else ""
    )
    from_businessconnection = (
        msg.business_connection_id
        if msg is not None
        else (
            update.business_connection.id
            if update.business_connection is not None
            else (
                update.deleted_business_messages.business_connection_id
                if update.deleted_business_messages is not None
                else ""
            )
        )
    ) or ""
    from_boostcount = (msg.sender_boost_count or 0) if msg is not None else 0
    from_signature = (msg.author_signature or "") if msg is not None else ""

    to_bot = True
    to_firstname = context.bot.first_name
    to_lastname = context.bot.last_name or ""
    to_username = context.bot.username

    chat_id = (
        chat.id
        if chat is not None
        else (
            update.business_connection.user_chat_id
            if update.business_connection is not None
            else 0
        )
    )
    chat_username = (chat.username or "") if chat is not None else ""
    chat_title = (chat.title or "") if chat is not None else ""
    chat_firstname = (chat.first_name or "") if chat is not None else ""
    chat_lastname = (chat.last_name or "") if chat is not None else ""
    chat_type = chat_type_

    message_type = message_type_
    message_id = (
        msg.id
        if msg is not None
        else (
            update.message_reaction.message_id
            if update.message_reaction is not None
            else (
                update.message_reaction_count.message_id
                if update.message_reaction_count is not None
                else 0
            )
        )
    )
    message_threadid = (msg.message_thread_id or 0) if msg is not None else 0
    message_date = (
        to_iso_string(msg.date)
        if msg is not None
        else to_iso_string(datetime.fromtimestamp(0))
    )
    message_topic = (msg.is_topic_message or False) if msg is not None else False
    message_automaticforward = (
        (msg.is_automatic_forward or False) if msg is not None else False
    )
    message_effectid = (msg.effect_id or "") if msg is not None else ""
    message_replytomessageid = (
        (msg.external_reply.message_id or 0)
        if msg is not None and msg.external_reply is not None
        else 0
    )
    message_quotetext = (
        (msg.quote.text or "") if msg is not None and msg.quote is not None else ""
    )

    forward_date = (
        to_iso_string(msg.forward_origin.date)
        if msg is not None and msg.forward_origin is not None
        else to_iso_string(datetime.fromtimestamp(0))
    )
    forward_from = forward_from_
    forward_messageid = (
        msg.forward_origin.message_id
        if msg is not None
        and msg.forward_origin is not None
        and hasattr(msg.forward_origin, "message_id")
        else 0
    )
    forward_signature = (
        msg.forward_origin.author_signature
        if msg is not None
        and msg.forward_origin is not None
        and hasattr(msg.forward_origin, "author_signature")
        else ""
    )
    forward_bot = (
        msg.forward_origin.sender_user.is_bot
        if msg is not None
        and msg.forward_origin is not None
        and hasattr(msg.forward_origin, "sender_user")
        else False
    )
    forward_name = forward_name_

    message_text = (msg.text or "") if msg is not None else ""

    message_url = (
        msg.link_preview_options.url
        if msg is not None
        and msg.link_preview_options is not None
        and isinstance(msg.link_preview_options.url, str)
        else ""
    )

    dice_emoji = msg.dice.emoji if msg is not None and msg.dice is not None else ""
    dice_value = msg.dice.value if msg is not None and msg.dice is not None else 0
    callbackquery_id = (
        update.callback_query.id if update.callback_query is not None else ""
    )
    callbackquery_inlinemessageid = (
        update.callback_query.inline_message_id
        if update.callback_query is not None
        else ""
    ) or ""
    callbackquery_data = (
        update.callback_query.data if update.callback_query is not None else ""
    ) or ""

    inlinequery_id = update.inline_query.id if update.inline_query is not None else ""
    inlinequery_text = (
        update.inline_query.query if update.inline_query is not None else ""
    )
    inlinequery_offset = (
        update.inline_query.offset if update.inline_query is not None else ""
    )

    inlineresultchosen_id = (
        update.chosen_inline_result.result_id
        if update.chosen_inline_result is not None
        else ""
    )
    inlineresultchosen_query = (
        update.chosen_inline_result.query
        if update.chosen_inline_result is not None
        else ""
    )
    inlineresultchosen_inlinemessageid = (
        update.chosen_inline_result.inline_message_id
        if update.chosen_inline_result is not None
        else ""
    ) or ""

    chatmember_id = (
        update.chat_member.new_chat_member.user.id
        if update.chat_member is not None
        else 0
    )
    chatmember_bot = (
        update.chat_member.new_chat_member.user.is_bot
        if update.chat_member is not None
        else False
    )
    chatmember_firstname = (
        update.chat_member.new_chat_member.user.first_name
        if update.chat_member is not None
        else ""
    )
    chatmember_lastname = (
        update.chat_member.new_chat_member.user.last_name
        if update.chat_member is not None
        else ""
    ) or ""
    chatmember_username = (
        update.chat_member.new_chat_member.user.username
        if update.chat_member is not None
        else ""
    ) or ""
    chatmember_premium = (
        update.chat_member.new_chat_member.user.is_premium
        if update.chat_member is not None
        else False
    ) or False
    chatmember_oldstatus = get_chat_member_status(
        update.chat_member.new_chat_member if update.chat_member is not None else None
    )
    chatmember_newstatus = get_chat_member_status(
        update.chat_member.old_chat_member if update.chat_member is not None else None
    )

    payload = update.to_json()

    return {
        "timestamp": timestamp,
        "type": type_,
        "to": to,
        "from": from_,
        "from_bot": from_bot,
        "from_firstname": from_firstname,
        "from_lastname": from_lastname,
        "from_username": from_username,
        "from_languagecode": from_languagecode,
        "from_premium": from_premium,
        "from_type": from_type,
        "from_title": from_title,
        "from_businessconnection": from_businessconnection,
        "from_boostcount": from_boostcount,
        "from_signature": from_signature,
        "to_bot": to_bot,
        "to_firstname": to_firstname,
        "to_lastname": to_lastname,
        "to_username": to_username,
        "chat_id": chat_id,
        "chat_username": chat_username,
        "chat_title": chat_title,
        "chat_firstname": chat_firstname,
        "chat_lastname": chat_lastname,
        "chat_type": chat_type,
        "message_type": message_type,
        "message_id": message_id,
        "message_threadid": message_threadid,
        "message_date": message_date,
        "message_topic": message_topic,
        "message_automaticforward": message_automaticforward,
        "message_effectid": message_effectid,
        "message_replytomessageid": message_replytomessageid,
        "message_quotetext": message_quotetext,
        "forward_date": forward_date,
        "forward_from": forward_from,
        "forward_messageid": forward_messageid,
        "forward_signature": forward_signature,
        "forward_bot": forward_bot,
        "forward_name": forward_name,
        "message_text": message_text,
        "message_url": message_url,
        "dice_emoji": dice_emoji,
        "dice_value": dice_value,
        "callbackquery_id": callbackquery_id,
        "callbackquery_inlinemessageid": callbackquery_inlinemessageid,
        "callbackquery_data": callbackquery_data,
        "inlinequery_id": inlinequery_id,
        "inlinequery_text": inlinequery_text,
        "inlinequery_offset": inlinequery_offset,
        "inlineresultchosen_id": inlineresultchosen_id,
        "inlineresultchosen_query": inlineresultchosen_query,
        "inlineresultchosen_inlinemessageid": inlineresultchosen_inlinemessageid,
        "chatmember_id": chatmember_id,
        "chatmember_bot": chatmember_bot,
        "chatmember_firstname": chatmember_firstname,
        "chatmember_lastname": chatmember_lastname,
        "chatmember_username": chatmember_username,
        "chatmember_premium": chatmember_premium,
        "chatmember_oldstatus": chatmember_oldstatus,
        "chatmember_newstatus": chatmember_newstatus,
        "payload": payload,
    }


def get_chat_member_status(chat_member: Optional[ChatMember]) -> ChatMemberStatus:
    if chat_member is None:
        return ChatMemberStatus.Unknown
    elif chat_member.status == "creator":
        return ChatMemberStatus.Creator
    elif chat_member.status == "administrator":
        return ChatMemberStatus.Administrator
    elif chat_member.status == "member":
        return ChatMemberStatus.Member
    elif chat_member.status == "restricted":
        return ChatMemberStatus.Restricted
    elif chat_member.status == "left":
        return ChatMemberStatus.Left
    elif chat_member.status == "kicked":
        return ChatMemberStatus.Banned
    else:
        return ChatMemberStatus.Unknown


# https://stackoverflow.com/a/63894149
def to_iso_string(datetime: datetime):
    return (
        datetime.astimezone(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )
