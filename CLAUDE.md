# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

This project uses **UV** for package management. Python >= 3.14 is required.

```bash
# Run the application
uv run python src/main.py

# Add a dependency
uv add <package>

# Run a script directly
uv run python <script>
```

## Architecture

**Exam practice app** — reads multiple-choice questions from JSON files in `data/` and presents them to the user.

- `src/main.py` — application entry point (currently a placeholder).
- `data/questions-1.json` — question bank. Each question follows this schema:
  - `type`: `"multiple-choices"`
  - `stem`: the question text
  - `choices`: array of option strings
  - `answer`: array of correct answer strings (supports multiple correct answers)

## Data Format

When adding new question files, follow the same JSON structure. The `answer` field is always an array, even for single-answer questions.
