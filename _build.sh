#!/usr/bin/bash

deno run -A _build.ts && deno fmt grammy.node.ts
deno run -A _generate_python_entry.ts
deno run -A _generate_python_enums.ts
ruff format python
