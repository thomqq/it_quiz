from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class QuizQuestion:
    slug: str
    prompt: str
    options: dict[str, str]  # keys: A,B,C,D
    correct: str
    detail: str
    image_path: Path


class QuizRepository:
    def __init__(self, questions_dir: Path) -> None:
        self._questions_dir = questions_dir

    @property
    def questions_dir(self) -> Path:
        return self._questions_dir

    def list_slugs(self) -> list[str]:
        if not self._questions_dir.exists():
            return []
        return sorted([p.name for p in self._questions_dir.iterdir() if p.is_dir()])

    def get_question(self, slug: str) -> QuizQuestion | None:
        slug_dir = self._questions_dir / slug
        if not slug_dir.is_dir():
            return None

        answer_path = slug_dir / "answer.txt"
        image_path = slug_dir / "question.png"
        if not answer_path.exists() or not image_path.exists():
            return None

        meta = self._parse_kv_file(answer_path)
        correct = meta.get("correct", "")
        options = {k: meta.get(k, "") for k in ("A", "B", "C", "D")}
        if correct not in {"A", "B", "C", "D"}:
            return None

        return QuizQuestion(
            slug=slug,
            prompt=meta.get("prompt", ""),
            options=options,
            correct=correct,
            detail=meta.get("detail", ""),
            image_path=image_path,
        )

    def get_image_bytes(self, slug: str) -> bytes | None:
        q = self.get_question(slug)
        if not q:
            return None
        try:
            return q.image_path.read_bytes()
        except OSError:
            return None

    def get_image_data_url(self, slug: str) -> str | None:
        image_bytes = self.get_image_bytes(slug)
        if image_bytes is None:
            return None
        b64 = base64.b64encode(image_bytes).decode("ascii")
        return f"data:image/png;base64,{b64}"

    @staticmethod
    def _parse_kv_file(path: Path) -> dict[str, str]:
        data: dict[str, str] = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
        return data
