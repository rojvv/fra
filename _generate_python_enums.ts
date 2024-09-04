import { join } from "jsr:@std/path";
import { ChatMemberStatus } from "./entry/chat_member_status.ts";
import { ChatType } from "./entry/chat_type.ts";
import { MessageType } from "./entry/message_type.ts";
import { UpdateType } from "./entry/update_type.ts";

const enums = [
  {
    name: "ChatMemberStatus",
    slug: "chat_member_status",
    enum: ChatMemberStatus,
  },
  {
    name: "ChatType",
    slug: "chat_type",
    enum: ChatType,
  },
  {
    name: "MessageType",
    slug: "message_type",
    enum: MessageType,
  },
  {
    name: "UpdateType",
    slug: "update_type",
    enum: UpdateType,
  },
];

for (const { name, slug, enum: enum_ } of enums) {
  const code = `
from enum import IntEnum

${name} = IntEnum(
    "${name}",
    [${
    Object.keys(enum_).filter((v) => isNaN(Number(v))).map((v) => `"${v}"`)
      .join(", ")
  }],
    start=0,
)

__all__ = ["${name}"]
    `.trim() + "\n";
  const fileName = join(
    import.meta.dirname + "",
    "python",
    "enums",
    slug + ".py",
  );
  Deno.writeTextFileSync(fileName, code);
}

let code = "";

for (const enum_ of enums) {
  code += `from .${enum_.slug} import ${enum_.name}\n`;
}

code += "\n__all__ = ";
code += "[" + enums.map((v) => v.name).map((v) => `"${v}"`).join(", ") + "]\n";

Deno.writeTextFileSync(
  join(import.meta.dirname + "", "python", "enums", "__init__.py"),
  code,
);
