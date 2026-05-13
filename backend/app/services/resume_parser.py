from __future__ import annotations

import io
import re
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document

SUPPORTED_EXTS = {".pdf", ".txt", ".md", ".docx"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

SKILL_KEYWORDS = [
    "python", "fastapi", "flask", "django", "sqlalchemy", "postgresql", "mysql",
    "mongodb", "redis", "docker", "kubernetes", "aws", "gcp", "azure", "rag",
    "langchain", "pandas", "numpy", "machine learning", "llm", "git", "ci/cd"
]

ROLE_HINT_RULES: dict[str, list[str]] = {
    "backend": ["fastapi", "flask", "django", "sqlalchemy", "postgresql", "redis", "docker"],
    "data": ["pandas", "numpy", "machine learning", "python"],
    "ml": ["machine learning", "llm", "rag", "python"],
}


def _clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _extract_text_from_pdf(content: bytes) -> str:
    pages: list[str] = []
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            pages.append(page.get_text("text") or "")
    return _clean_text("\n".join(pages))


def _extract_text_from_docx(content: bytes) -> str:
    document = Document(io.BytesIO(content))
    lines = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    return _clean_text("\n".join(lines))


def extract_resume_text(filename: str, content: bytes) -> str:
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise ValueError("File too large. Max size is 10MB.")

    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTS:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == ".pdf":
        return _extract_text_from_pdf(content)

    if ext in {".txt", ".md"}:
        return _clean_text(content.decode("utf-8", errors="ignore"))

    if ext == ".docx":
        return _extract_text_from_docx(content)

    raise ValueError(f"Unsupported file type: {ext}")


def _extract_email(text: str) -> str | None:
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> str | None:
    m = re.search(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}", text)
    return m.group(0) if m else None


def _extract_links(text: str) -> list[str]:
    links = re.findall(r"https?://[^\s)]+", text)
    # Deduplicate while preserving order
    seen = set()
    out: list[str] = []
    for link in links:
        if link not in seen:
            seen.add(link)
            out.append(link)
    return out


def _extract_name(text: str) -> str | None:
    # Heuristic: first non-empty short line without '@' and not all caps headings
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "@" in line:
            continue
        if len(line) > 60:
            continue
        if re.search(r"(skills|experience|education|projects|summary)", line, flags=re.I):
            continue
        return line
    return None


def _extract_years_experience(text: str) -> int | None:
    m = re.search(r"(\d{1,2})\+?\s+years", text, flags=re.I)
    if m:
        return int(m.group(1))
    return None


def _extract_skills(text: str) -> list[str]:
    t = text.lower()
    found = [s for s in SKILL_KEYWORDS if s in t]
    return sorted(set(found), key=found.index)


def _infer_roles(skills: list[str], target_role: str | None = None) -> list[str]:
    if target_role:
        return [target_role.strip().lower()]

    skill_set = set(skills)
    inferred: list[str] = []
    for role, cues in ROLE_HINT_RULES.items():
        if any(c in skill_set for c in cues):
            inferred.append(role)

    return inferred or ["backend"]


def parse_resume(text: str, target_role: str | None = None) -> tuple[dict, dict, list[str]]:
    profile = {
        "full_name": _extract_name(text),
        "email": _extract_email(text),
        "phone": _extract_phone(text),
        "years_experience": _extract_years_experience(text),
        "skills": _extract_skills(text),
        "target_roles": [],
        "links": _extract_links(text),
    }
    profile["target_roles"] = _infer_roles(profile["skills"], target_role)

    required = ["full_name", "email", "skills"]
    missing_fields = []
    for key in required:
        val = profile.get(key)
        if val is None or (isinstance(val, list) and len(val) == 0):
            missing_fields.append(key)

    confidence = {
        "overall": round((len(required) - len(missing_fields)) / len(required), 2),
        "name": 1.0 if profile["full_name"] else 0.0,
        "email": 1.0 if profile["email"] else 0.0,
        "skills": 1.0 if profile["skills"] else 0.0,
    }

    return profile, confidence, missing_fields
