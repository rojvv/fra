import { Project } from "@ts-morph/ts-morph";
import { Z_Entry } from "./entry.zod.ts";
Deno.writeTextFileSync(
  "entry_keys.ts",
  `export const ENTRY_KEYS = [
${Object.keys(Z_Entry._def.shape()).map((v) => `  "${v}",\n`).join("")}];\n`,
);

const project = new Project();

const OUT_FILE = "grammy.node.ts";

const sourceFile = project.addSourceFileAtPath("./grammy.ts")
  .copy(OUT_FILE, { overwrite: true });

const REPLACE_IMPORTS = {
  "https://deno.land/x/grammy@v1.29.0/mod.ts": "grammy",
  "https://deno.land/x/grammy@v1.29.0/types.ts": "grammy/types",
} as Record<string, string>;

for (const i of sourceFile.getImportDeclarations()) {
  const spec = i.getModuleSpecifier().getLiteralText();
  if (spec in REPLACE_IMPORTS) {
    i.setModuleSpecifier(REPLACE_IMPORTS[spec]);
  }
}

sourceFile.saveSync();

const ENTRY_FILE = OUT_FILE;
const files = [ENTRY_FILE];
const content = [];
const done = new Array<string>();

while (files.length) {
  const file = files.shift()!;
  const sourceFile = project.addSourceFileAtPath(file);
  if (done.includes(sourceFile.getFilePath())) {
    continue;
  }

  for (const i of sourceFile.getImportDeclarations()) {
    const spec = i.getModuleSpecifier().getLiteralText();
    if (spec.includes(".")) {
      files.push(spec);
      i.remove();
    }
  }

  done.push(sourceFile.getFilePath());
  content.push(sourceFile.getText());
}

content.reverse();

Deno.writeTextFileSync(OUT_FILE, content.join("\n"));
