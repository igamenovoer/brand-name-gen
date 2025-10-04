# AI Assistant Guide

Use the `context/` directory for all collaborative artifacts: design notes, plans, logs, tasks, summaries, and role prompts. Start new documents with the HEADER section (purpose, status, date, dependencies, target).

Quick tips:
- Review `context/README.md` for structure and conventions.
- Prefer editing context docs alongside code changes to keep knowledge current.
- Use `pixi` tasks for dev workflows (lint, typecheck, test, build, docs).

Key commands:
```
pixi run quality
pixi run build
pixi run docs-serve
```

