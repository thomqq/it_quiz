from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for

from quiz_repository import QuizRepository

app = Flask(__name__)


BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_DIR = BASE_DIR / "data" / "questions"
repo = QuizRepository(QUESTIONS_DIR)


@app.get("/")
def hello_world():
    return "Hello, World!"


@app.get("/data/questions/<path:filename>")
def questions_asset(filename: str):
    # Serves PNG files from data/questions/... (no secrets should be stored there)
    return send_from_directory(repo.questions_dir, filename)


@app.get("/api/questions")
def api_questions_list():
    return jsonify({"questions": repo.list_slugs()})


@app.get("/api/questions/<slug>")
def api_question(slug: str):
    q = repo.get_question(slug)
    if not q:
        return jsonify({"error": "not_found"}), 404

    include_image = request.args.get("include_image") in {"1", "true", "yes"}
    payload = {
        "slug": q.slug,
        "prompt": q.prompt,
        "options": q.options,
        # Do not expose the correct answer by default.
        "image_url": url_for("questions_asset", filename=f"{slug}/question.png", _external=True),
    }

    if include_image:
        payload["image_data_url"] = repo.get_image_data_url(slug)

    return jsonify(payload)


@app.get("/quiz")
def quiz_page():
    slugs = repo.list_slugs()
    if not slugs:
        return (
            "No questions found. Generate them with: python scripts/generate_questions.py",
            500,
        )

    slug = request.args.get("q") or slugs[0]
    if slug not in slugs:
        slug = slugs[0]

    q = repo.get_question(slug)
    if not q:
        return (
            f"Question '{slug}' is missing required files. Re-generate with: python scripts/generate_questions.py",
            500,
        )

    image_url = url_for("questions_asset", filename=f"{slug}/question.png")
    return render_template(
        "quiz.html",
        slug=slug,
        image_url=image_url,
        prompt=q.prompt,
    )


@app.post("/quiz")
def quiz_submit():
    selected = request.form.get("answer")
    if selected not in {"A", "B", "C", "D"}:
        return redirect(url_for("quiz_page"))

    slug = request.form.get("slug")
    if not slug:
        return redirect(url_for("quiz_page"))

    q = repo.get_question(slug)
    if not q:
        return redirect(url_for("quiz_page"))

    correct = q.correct
    detail = q.detail

    slugs = repo.list_slugs()
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
