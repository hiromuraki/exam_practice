"""Exam practice app — FastAPI backend.

Reads questions from data/*.json and serves randomized practice sets.
"""

import json
import random
import string
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Exam Practice")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _normalise(q: dict) -> dict:
    """Normalise a question dict so it always has ``stem``, ``choices``, ``answer``."""
    stem = q.get("stem") or q.get("stem:", "") or ""
    choices = q.get("choices") or q.get("choice") or []
    answer = q.get("answer") or []
    return {"stem": stem, "choices": list(choices), "answer": list(answer)}


def _load_all() -> list[dict]:
    questions: list[dict] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                questions.extend(_normalise(q) for q in data)
            else:
                questions.append(_normalise(data))
    return questions


QUESTION_POOL = _load_all()

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@app.get("/api/practice")
def get_practice(n: int = Query(20, ge=1, le=200)):
    """Return a randomised practice set of *n* questions (without answers)."""
    pool = list(QUESTION_POOL)
    random.shuffle(pool)
    selected = pool[: min(n, len(pool))]

    result = []
    for q in selected:
        choices = list(q["choices"])
        random.shuffle(choices)
        labels = list(string.ascii_uppercase[: len(choices)])
        result.append(
            {
                "stem": q["stem"],
                "choices": [f"{l}. {c}" for l, c in zip(labels, choices)],
                "choice_values": choices,  # raw text (no label), same order
                "labels": labels,
                "answer_count": len(q["answer"]),
            }
        )

    return {"questions": result, "total": len(result)}


class AnswerItem(BaseModel):
    stem: str
    selected: list[str]


class CheckRequest(BaseModel):
    answers: list[AnswerItem]


@app.post("/api/check")
def check_answers(body: CheckRequest):
    """Validate user answers against the question pool."""
    results: list[dict] = []
    correct_count = 0

    for item in body.answers:
        # Find the question in the pool
        q = _find_question(item.stem)
        if q is None:
            results.append(
                {"stem": item.stem, "correct": False, "expected": [], "detail": "not found"}
            )
            continue

        expected = sorted(q["answer"])
        user = sorted(item.selected)
        is_correct = user == expected
        if is_correct:
            correct_count += 1
        results.append(
            {
                "stem": item.stem,
                "correct": is_correct,
                "expected": q["answer"],
            }
        )

    total = len(results)
    return {
        "results": results,
        "stats": {
            "correct": correct_count,
            "total": total,
            "rate": round(correct_count / total * 100, 1) if total else 0.0,
        },
    }


def _find_question(stem: str) -> dict | None:
    """Return the *unedited* pool question whose stem matches."""
    for q in QUESTION_POOL:
        if q["stem"] == stem:
            return q
    return None


# ---------------------------------------------------------------------------
# Serve static frontend
# ---------------------------------------------------------------------------

if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
