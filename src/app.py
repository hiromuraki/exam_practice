"""Exam practice app — FastAPI backend.

Reads questions from data/*.json and serves randomized practice sets.
"""

import hashlib
import json
import os
import random
import string
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Exam Practice")

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _normalise(q: dict) -> dict:
    """Normalise a question dict so it always has ``type``, ``stem``, ``choices``, ``answer``."""
    stem = q.get("stem") or q.get("stem:", "") or ""
    choices = q.get("choices") or q.get("choice") or []
    raw_answer = q.get("answer") or []

    # answer is always stored as a list (judgement may be a bare string)
    if isinstance(raw_answer, str):
        answer = [raw_answer]
    else:
        answer = list(raw_answer)

    qid = hashlib.md5(stem.encode("utf-8")).hexdigest()
    return {
        "id": qid,
        "type": q.get("type", "multiple-choice"),
        "stem": stem,
        "choices": list(choices),
        "answer": answer,
    }


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


def _pool_counts() -> dict[str, int]:
    """Return {label: count} breakdown of the full question pool."""
    counts: dict[str, int] = {}
    for q in QUESTION_POOL:
        t = q.get("type", "multiple-choice")
        if t == "multiple-choice":
            label = "单选" if len(q.get("answer", [])) == 1 else "多选"
        elif t == "judgement":
            label = "判断"
        elif t == "cloze":
            label = "填空"
        else:
            label = t
        counts[label] = counts.get(label, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


@app.get("/api/pool-info")
def get_pool_info():
    """Return pool-level stats (no questions)."""
    return {
        "pool_total": len(QUESTION_POOL),
        "pool_counts": _pool_counts(),
    }


class PracticeRequest(BaseModel):
    n: int = 20
    mastered_ids: list[str] = []


@app.post("/api/practice")
def get_practice(body: PracticeRequest):
    """Return a randomised practice set.

    Questions whose id is in *mastered_ids* are deprioritised: they are only
    included when the non-mastered pool is smaller than *n*.
    """
    mastered = set(body.mastered_ids)
    fresh = [q for q in QUESTION_POOL if q["id"] not in mastered]
    mastered_pool = [q for q in QUESTION_POOL if q["id"] in mastered]

    remaining = len(fresh)
    random.shuffle(fresh)
    random.shuffle(mastered_pool)

    # Take from fresh first, then supplement from mastered if needed
    selected = fresh[: body.n]
    if len(selected) < body.n:
        needed = body.n - len(selected)
        selected += mastered_pool[:needed]
    random.shuffle(selected)

    result = []
    for q in selected:
        qtype = q["type"]

        if qtype == "judgement":
            result.append(
                {
                    "id": q["id"],
                    "stem": q["stem"],
                    "type": "judgement",
                    "choices": ["正确 (True)", "错误 (False)"],
                    "choice_values": ["TRUE", "FALSE"],
                    "answer_count": 1,
                }
            )

        elif qtype == "cloze":
            result.append(
                {
                    "id": q["id"],
                    "stem": q["stem"],
                    "type": "cloze",
                    "answer_count": len(q["answer"]),
                }
            )

        else:  # multiple-choice (default)
            choices = list(q["choices"])
            random.shuffle(choices)
            labels = list(string.ascii_uppercase[: len(choices)])
            result.append(
                {
                    "id": q["id"],
                    "stem": q["stem"],
                    "type": "multiple-choice",
                    "choices": [f"{l}. {c}" for l, c in zip(labels, choices)],
                    "choice_values": choices,  # raw text (no label), same order
                    "labels": labels,
                    "answer_count": len(q["answer"]),
                }
            )

    return {
        "questions": result,
        "total": len(result),
        "pool_total": len(QUESTION_POOL),
        "remaining": remaining,
        "pool_counts": _pool_counts(),
    }


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

        qtype = q.get("type", "multiple-choice")

        if qtype == "cloze":
            # Case-insensitive, whitespace-trimmed comparison for fill-in-blanks
            user_vals = [v.strip().lower() for v in item.selected]
            expected_vals = [v.strip().lower() for v in q["answer"]]
            is_correct = user_vals == expected_vals
        else:
            # Exact match for multiple-choice and judgement
            expected_vals = sorted(q["answer"])
            user_vals = sorted(item.selected)
            is_correct = user_vals == expected_vals

        if is_correct:
            correct_count += 1
        results.append(
            {
                "id": q["id"],
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
