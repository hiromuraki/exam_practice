# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

This project uses **UV** for package management. Python >= 3.14 is required.

```bash
# Run the application
uv run uvicorn src.app:app --host 127.0.0.1 --port 8000

# Add a dependency
uv add <package>

# Run a script directly
uv run python <script>
```

## Architecture

**Exam practice app** — FastAPI backend + vanilla JS SPA frontend. Reads questions from `data/*.json` and serves randomised practice sets with mastery tracking.

- `src/app.py` — FastAPI application (all backend logic).
- `static/index.html` — single-page frontend (HTML + inline CSS + inline JS).
- `data/*.json` — question bank files.

### Question types

| type | UI control | answer format | validation |
| --- | --- | --- | --- |
| `multiple-choice` | radio (single) / checkbox (multi) | `["option text"]` | exact match |
| `judgement` | radio: 正确(True) / 错误(False) | `"TRUE"` or `"FALSE"` (string, normalised to list) | exact match |
| `cloze` | text input | `["expected text"]` | case-insensitive, whitespace-trimmed |

Each question gets a unique `id` (MD5 of its `stem`). The `answer` field is always normalised to `list[str]` internally — judgement answers in JSON may be a bare string.

### API endpoints

| method | path | purpose |
| --- | --- | --- |
| `GET` | `/api/pool-info` | return pool size and type-count breakdown |
| `POST` | `/api/practice` | return N randomised questions; body: `{n, mastered_ids}` — deprioritises mastered IDs, supplements from them when the fresh pool is too small |
| `POST` | `/api/check` | validate answers; returns per-question correctness + stats |

Static files are mounted at `/` via `StaticFiles(html=True)`.

### Frontend state

- **Three-column layout**: left history sidebar (0 → 320px), center main content (flex: 1), right result sidebar (0 → 380px). No overlays.
- **localStorage**:
  - `exam_practice_correct` — `{id: count}` of correct answers per question
  - `exam_practice_meta` — `{id: {s: stem, t: type}}` for history display only
- **Mastery threshold**: a question is "mastered" after being answered correctly ≥ 3 times; only then is it excluded from future practice draws.

## Data format

Questions in `data/*.json` are arrays of objects. Common fields:

- `type`: `"multiple-choice"` | `"judgement"` | `"cloze"`
- `stem`: question text
- `answer`: correct answer(s) — array of strings (judgement may be bare `"TRUE"`/`"FALSE"`)
- `choice` or `choices` (multiple-choice only): option strings

The normaliser also handles `"stem:"` (trailing colon) as an alias for `"stem"`.
