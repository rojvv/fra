import { join } from "jsr:@std/path";
import { Z_Entry } from "./entry.zod.ts";
import z from "zod";

let code = `
from typing import TypedDict
from .enums import *


Entry = TypedDict(
    "Entry",
    {
`;

for (const [k, v] of Object.entries(Z_Entry._def.shape())) {
  let type = "...";
  if (v instanceof z.ZodString) {
    type = "str";
  } else if (v instanceof z.ZodBoolean) {
    type = "bool";
  } else if (v instanceof z.ZodNumber) {
    type = "int";
  } else if (v instanceof z.ZodIntersection) {
    const desc = v._def.right.description;
    if (desc && desc.startsWith("enum_")) {
      type = desc.slice("enum_".length);
    } else if (v._def.left instanceof z.ZodNumber) {
      [
        type = "int",
      ];
    }
  }
  code += `        "${k}": ${type},\n`;
}
code += `    }
)`;

Deno.writeTextFileSync(
  join(import.meta.dirname + "", "python", "entry.py"),
  code.trim() + "\n",
);
