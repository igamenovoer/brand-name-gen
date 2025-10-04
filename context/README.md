# Project Context

## HEADER
- **Purpose**: Centralize project knowledge for AI-assisted development
- **Status**: Active
- **Date**: 2025-10-04
- **Dependencies**: None
- **Target**: AI assistants and developers

## Content
This `context/` directory is a structured knowledge base designed to help AI assistants and developers collaborate effectively. It organizes design docs, prompts, logs, plans, and other materials needed for efficient, consistent work.

### Structure
```
context/
├── design/          # Technical specifications and architecture
├── hints/           # How-to guides and troubleshooting tips
├── instructions/    # Reusable prompt snippets and commands
├── logs/            # Development session records and outcomes
├── plans/           # Implementation roadmaps and strategies
├── refcode/         # Reference implementations and examples
├── roles/           # Role-based system prompts and memory
├── summaries/       # Knowledge base and analysis documents
├── tasks/           # Current and planned work items
│   ├── features/    # Feature implementation tasks
│   ├── fixes/       # Bug fix tasks
│   ├── refactor/    # Code refactoring tasks
│   └── tests/       # Testing-related tasks
└── tools/           # Custom development utilities
```

### Usage
- Add documents following the HEADER format at the top of each file.
- Keep content current; mark outdated docs as deprecated in the header.
- Use the subdirectory READMEs below for guidance on what to place where.

### Reference
This layout follows `magic-context/general/context-dir-guide.md` and aligns with best practices for AI-first development workflows.

