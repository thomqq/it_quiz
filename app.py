from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, send_from_directory, session, url_for

from quiz_repository import QuizRepository
from quiz_service import QuizProgressService

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")


BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_DIR = BASE_DIR / "data" / "questions"
repo = QuizRepository(QUESTIONS_DIR)
progress = QuizProgressService(repo)


@app.get("/")
def hello_world():
    return "Hello, World!"


@app.get("/data/questions/<path:filename>")
def questions_asset(filename: str):
    # Serves PNG files from data/questions/... (no secrets should be stored there)
    resp = send_from_directory(repo.questions_dir, filename)
    # Avoid confusing browser caching when moving between questions quickly.
    resp.headers["Cache-Control"] = "no-store"
    return resp


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

    requested_slug = request.args.get("q")
    if requested_slug:
        slug = progress.set_current_slug(session, requested_slug)
    else:
        slug = progress.get_or_init_current_slug(session)

    if not slug:
        return (
            "No questions found. Generate them with: python scripts/generate_questions.py",
            500,
        )

    q = repo.get_question(slug)
    if not q:
        return (
            f"Question '{slug}' is missing required files. Re-generate with: python scripts/generate_questions.py",
            500,
        )

    try:
        cache_bust = q.image_path.stat().st_mtime_ns
    except OSError:
        cache_bust = 0

    image_url = url_for(
        "questions_asset",
        filename=f"{slug}/question.png",
        v=cache_bust,
    )
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
        return redirect(url_for("quiz_page"), code=303)

    slug_from_form = request.form.get("slug")
    current_slug = progress.get_or_init_current_slug(session)
    if not current_slug:
        return redirect(url_for("quiz_page"), code=303)

    if slug_from_form and slug_from_form != current_slug:
        flash("Question changed. Please answer the current question.")
        return redirect(url_for("quiz_page", q=current_slug), code=303)

    result = progress.submit(session, current_slug, selected)
    if not result:
        return redirect(url_for("quiz_page"), code=303)

    if result.is_correct:
        flash("Correct. Moving to the next question.")
        return redirect(url_for("quiz_page", q=result.next_slug), code=303)

    flash(f"Incorrect. Correct answer is {result.correct}. {result.detail}")
    return redirect(url_for("quiz_page", q=current_slug), code=303)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
