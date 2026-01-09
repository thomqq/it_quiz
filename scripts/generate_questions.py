from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


@dataclass(frozen=True)
class Question:
    slug: str
    prompt: str
    options: list[str]  # A..D
    correct: str  # "A"|"B"|"C"|"D"
    detail: str


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Best-effort font selection (macOS + fallback)
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Verdana.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for font_path in candidates:
        p = Path(font_path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []

    for word in words:
        test = " ".join([*current, word])
        width = draw.textlength(test, font=font)
        if width <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
                current = [word]
            else:
                lines.append(word)

    if current:
        lines.append(" ".join(current))
    return lines


def render_question_png(out_path: Path, q: Question) -> None:
    width, height = 1000, 560
    padding = 40

    img = Image.new("RGB", (width, height), (250, 250, 252))
    draw = ImageDraw.Draw(img)

    title_font = _find_font(34)
    body_font = _find_font(26)
    mono_font = _find_font(24)

    # Card
    card_bbox = (20, 20, width - 20, height - 20)
    draw.rounded_rectangle(card_bbox, radius=18, fill=(255, 255, 255), outline=(220, 220, 220), width=2)

    x = 20 + padding
    y = 20 + padding
    max_text_width = width - 40 - 2 * padding

    draw.text((x, y), f"Quiz ({q.slug})", font=mono_font, fill=(90, 90, 90))
    y += 42

    # Prompt
    prompt_lines = _wrap_text(draw, q.prompt, title_font, max_text_width)
    for line in prompt_lines:
        draw.text((x, y), line, font=title_font, fill=(20, 20, 20))
        y += 42

    y += 10

    # Options
    for idx, option_text in enumerate(q.options):
        letter = chr(ord("A") + idx)
        option_line = f"{letter}) {option_text}"
        option_lines = _wrap_text(draw, option_line, body_font, max_text_width)
        for j, line in enumerate(option_lines):
            draw.text((x, y), line, font=body_font, fill=(35, 35, 35))
            y += 34
        y += 8

    # Footer hint
    hint = "Choose A, B, C, or D in the form"
    draw.text((x, height - 20 - padding - 24), hint, font=mono_font, fill=(120, 120, 120))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")


def write_answer_file(out_path: Path, q: Question) -> None:
    content = (
        f"correct={q.correct}\n"
        f"detail={q.detail}\n"
        f"prompt={q.prompt}\n"
        f"A={q.options[0]}\n"
        f"B={q.options[1]}\n"
        f"C={q.options[2]}\n"
        f"D={q.options[3]}\n"
    )
    out_path.write_text(content, encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    questions_dir = base_dir / "data" / "questions"

    questions: list[Question] = [
        Question(
            slug="q01",
            prompt="Which HTTP method is typically used to retrieve data?",
            options=["POST", "GET", "DELETE", "PATCH"],
            correct="B",
            detail="GET is designed for retrieving resources without side effects.",
        ),
        Question(
            slug="q02",
            prompt="Which command shows the current working directory in a Unix shell?",
            options=["ls", "pwd", "cd", "whoami"],
            correct="B",
            detail="pwd prints the absolute path of the current directory.",
        ),
        Question(
            slug="q03",
            prompt="What does DNS translate?",
            options=["Domain names to IP addresses", "IP addresses to MAC addresses", "Passwords to hashes", "Files to folders"],
            correct="A",
            detail="DNS resolves domain names (like example.com) to IP addresses.",
        ),
        Question(
            slug="q04",
            prompt="Which port is the default for HTTPS?",
            options=["21", "80", "443", "8080"],
            correct="C",
            detail="HTTPS defaults to port 443.",
        ),
        Question(
            slug="q05",
            prompt="In Git, which command creates a new branch and switches to it?",
            options=["git init", "git checkout -b <name>", "git merge <name>", "git log"],
            correct="B",
            detail="git checkout -b creates and checks out a new branch in one step.",
        ),
        Question(
            slug="q06",
            prompt="Which of these is a strong password practice?",
            options=["Reusing the same password", "Using a password manager", "Sharing passwords by email", "Using only lowercase"],
            correct="B",
            detail="A password manager helps generate/store unique strong passwords.",
        ),
        Question(
            slug="q07",
            prompt="What does RAM stand for?",
            options=["Random Access Memory", "Read Access Machine", "Rapid Application Module", "Remote Access Memory"],
            correct="A",
            detail="RAM is Random Access Memory (volatile working memory).",
        ),
        Question(
            slug="q08",
            prompt="Which SQL clause filters rows?",
            options=["ORDER BY", "GROUP BY", "WHERE", "LIMIT"],
            correct="C",
            detail="WHERE filters rows based on conditions.",
        ),
        Question(
            slug="q09",
            prompt="In Python, what is the correct file extension for a module?",
            options=[".py", ".pym", ".python", ".pt"],
            correct="A",
            detail="Python source modules use the .py extension.",
        ),
        Question(
            slug="q10",
            prompt="Which protocol is commonly used to securely connect to a remote shell?",
            options=["FTP", "SSH", "Telnet", "HTTP"],
            correct="B",
            detail="SSH provides encrypted remote shell access.",
        ),
    ]

    for q in questions:
        q_dir = questions_dir / q.slug
        render_question_png(q_dir / "question.png", q)
        write_answer_file(q_dir / "answer.txt", q)

    print(f"Generated {len(questions)} questions in: {questions_dir}")


if __name__ == "__main__":
    main()
