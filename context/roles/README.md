# Roles

## HEADER
- **Purpose**: Maintain role-based system prompts, memory, and context for different AI personas
- **Status**: Active
- **Date**: 2025-10-04
- **Dependencies**: None
- **Target**: AI assistants and developers

## Content
Create one subdirectory per role. Each role directory typically includes:
- `system-prompt.md`: The role’s core instruction set
- `memory.md`: Accumulated knowledge specific to the role
- `context.md` or `knowledge-base.md`: Additional references for the role

Example layout:
```
roles/
  backend-developer/
    system-prompt.md
    memory.md
  frontend-specialist/
    system-prompt.md
    memory.md
```

