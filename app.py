from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_from_directory, url_for

app = Flask(__name__)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "questions"


def _list_question_slugs() -> list[str]:
    if not DATA_DIR.exists():
        return []
    return sorted([p.name for p in DATA_DIR.iterdir() if p.is_dir()])


def _load_answer_file(slug: str) -> dict[str, str] | None:
    answer_path = DATA_DIR / slug / "answer.txt"
    if not answer_path.exists():
        return None

    data: dict[str, str] = {}
    for raw_line in answer_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


@app.get("/")
def hello_world():
    return "Hello, World!"


@app.get("/data/questions/<path:filename>")
def questions_asset(filename: str):
    # Serves PNG files from data/questions/... (no secrets should be stored there)
    return send_from_directory(DATA_DIR, filename)


@app.get("/quiz")
def quiz_page():
    slugs = _list_question_slugs()
    if not slugs:
        return (
            "No questions found. Generate them with: python scripts/generate_questions.py",
            500,
        )

    slug = request.args.get("q") or slugs[0]
    if slug not in slugs:
        slug = slugs[0]

    meta = _load_answer_file(slug) or {}

    image_url = url_for("questions_asset", filename=f"{slug}/question.png")
    return render_template(
        "quiz.html",
        slug=slug,
        image_url=image_url,
        prompt=meta.get("prompt", ""),
    )


@app.post("/quiz")
def quiz_submit():
    selected = request.form.get("answer")
    if selected not in {"A", "B", "C", "D"}:
        return redirect(url_for("quiz_page"))

    slug = request.form.get("slug")
    if not slug:
        return redirect(url_for("quiz_page"))

    meta = _load_answer_file(slug)
    if not meta or meta.get("correct") not in {"A", "B", "C", "D"}:
        return redirect(url_for("quiz_page"))

    correct = meta["correct"]
    detail = meta.get("detail", "")

    slugs = _list_question_slugs()
    next_slug = None
    if slug in slugs:
        idx = slugs.index(slug)
        next_slug = slugs[(idx + 1) % len(slugs)]

    return render_template(
        "result.html",
        selected=selected,
        correct=correct,
        is_correct=(selected == correct),
        detail=detail,
        next_url=url_for("quiz_page", q=next_slug) if next_slug else url_for("quiz_page"),
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
