from __future__ import annotations

from dataclasses import dataclass

from quiz_repository import QuizRepository, QuizQuestion


@dataclass(frozen=True)
class SubmitResult:
    slug: str
    selected: str
    correct: str
    is_correct: bool
    detail: str
    next_slug: str


class QuizProgressService:
    SESSION_KEY = "quiz_current_slug"

    def __init__(self, repo: QuizRepository) -> None:
        self._repo = repo

    def get_or_init_current_slug(self, session: dict) -> str | None:
        slugs = self._repo.list_slugs()
        if not slugs:
            return None

        slug = session.get(self.SESSION_KEY)
        if slug in slugs:
            return slug

        session[self.SESSION_KEY] = slugs[0]
        return slugs[0]

    def set_current_slug(self, session: dict, slug: str) -> str | None:
        slugs = self._repo.list_slugs()
        if not slugs:
            return None
        if slug not in slugs:
            slug = slugs[0]
        session[self.SESSION_KEY] = slug
        return slug

    def submit(self, session: dict, slug: str, selected: str) -> SubmitResult | None:
        if selected not in {"A", "B", "C", "D"}:
            return None

        question = self._repo.get_question(slug)
        if not question:
            return None

        slugs = self._repo.list_slugs()
        next_slug = slug
        is_correct = selected == question.correct
        if is_correct and slug in slugs:
            idx = slugs.index(slug)
            next_slug = slugs[(idx + 1) % len(slugs)]

        # Session progression rule:
        # - incorrect -> stay on same question
        # - correct   -> advance to next
        session[self.SESSION_KEY] = next_slug

        return SubmitResult(
            slug=slug,
            selected=selected,
            correct=question.correct,
            is_correct=is_correct,
            detail=question.detail,
            next_slug=next_slug,
        )
