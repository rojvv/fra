import { z } from "zod";
import { Z_UpdateType } from "./entry/update_type.zod.ts";
import { Z_ChatType } from "./entry/chat_type.zod.ts";
import { Z_MessageType } from "./entry/message_type.zod.ts";
import { Z_ChatMemberStatus } from "./entry/chat_member_status.zod.ts";

export const Z_Entry = z.object({
  // generic
  timestamp: z.string().datetime(),
  type: Z_UpdateType,
  to: z.number(),
  from: z.number(),

  // Sender
  from_bot: z.boolean(),
  from_firstname: z.string(),
  from_lastname: z.string(),
  from_username: z.string(),
  from_languagecode: z.string(),
  from_premium: z.boolean(),
  from_type: Z_ChatType,
  from_title: z.string(),
  from_businessconnection: z.string(),
  from_boostcount: z.number(),
  from_signature: z.string(),

  // Receiver
  to_bot: z.boolean(),
  to_firstname: z.string(),
  to_lastname: z.string(),
  to_username: z.string(),

  // Chat
  chat_id: z.number(),
  chat_username: z.string(),
  chat_title: z.string(),
  chat_firstname: z.string(),
  chat_lastname: z.string(),
  chat_type: Z_ChatType,

  // Message
  message_type: Z_MessageType,
  message_id: z.number(),
  message_threadid: z.number(),
  message_date: z.string().datetime(),
  message_topic: z.boolean(),
  message_automaticforward: z.boolean(),
  message_effectid: z.string(),
  message_replytomessageid: z.number(),
  message_quotetext: z.string(),

  // Forward
  forward_date: z.string().datetime(),
  forward_from: z.number(),
  forward_messageid: z.number(),
  forward_signature: z.string(),
  forward_bot: z.boolean(),
  forward_name: z.string(),

  // Text message / media captions
  message_text: z.string(),

  // Link preview-only message
  message_url: z.string(),

  // Dice message
  dice_emoji: z.string(),
  dice_value: z.number(),

  // Callback query
  callbackquery_id: z.string(),
  callbackquery_inlinemessageid: z.string(),
  callbackquery_data: z.string(),

  // Inline query
  inlinequery_id: z.string(),
  inlinequery_text: z.string(),
  inlinequery_offset: z.string(),

  // Chosen inline result
  inlineresultchosen_id: z.string(),
  inlineresultchosen_query: z.string(),
  inlineresultchosen_inlinemessageid: z.string(),

  // Chat member updates
  chatmember_id: z.number(),
  chatmember_bot: z.boolean(),
  chatmember_firstname: z.string(),
  chatmember_lastname: z.string(),
  chatmember_username: z.string(),
  chatmember_premium: z.boolean(),
  chatmember_oldstatus: Z_ChatMemberStatus,
  chatmember_newstatus: Z_ChatMemberStatus,

  // library
  payload: z.string(),
});
