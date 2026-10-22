"""Skill synonym map and deterministic overlap scoring."""

from __future__ import annotations

import re
from typing import Iterable

# Canonical skill -> aliases (lowercase)
SKILL_SYNONYMS: dict[str, list[str]] = {
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "python": ["py"],
    "postgresql": ["postgres", "psql", "postgre"],
    "mongodb": ["mongo"],
    "react": ["reactjs", "react.js"],
    "nodejs": ["node", "node.js"],
    "django": ["django rest", "drf"],
    "docker": ["containerisation", "containerization"],
    "kubernetes": ["k8s"],
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp", "google cloud"],
    "microsoft azure": ["azure"],
    "ci/cd": ["cicd", "continuous integration", "continuous delivery"],
    "machine learning": ["ml", "apprentissage automatique"],
    "artificial intelligence": ["ai", "ia", "intelligence artificielle"],
    "sql": ["structured query language"],
    "html": ["html5"],
    "css": ["css3"],
    "git": ["github", "gitlab", "version control"],
    "rest api": ["rest", "restful", "api rest"],
    "agile": ["scrum", "kanban"],
    "java": ["jdk", "jvm"],
    "c++": ["cpp", "c plus plus"],
    "c#": ["csharp", "c sharp", ".net", "dotnet"],
}


def _build_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in SKILL_SYNONYMS.items():
        lookup[canonical.lower()] = canonical
        for alias in aliases:
            lookup[alias.lower()] = canonical
    return lookup


_LOOKUP = _build_lookup()


def normalize_skill(skill: str) -> str:
    cleaned = re.sub(r"\s+", " ", (skill or "").strip().lower())
    cleaned = cleaned.replace("_", " ")
    return _LOOKUP.get(cleaned, cleaned)


def canonicalize_skills(skills: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        if not skill or not str(skill).strip():
            continue
        norm = normalize_skill(str(skill))
        if norm not in seen:
            seen.add(norm)
            # Prefer title-ish display for known skills
            display = next(
                (k.title() if k.islower() else k for k, v in ((norm, norm),) if True),
                norm,
            )
            # Use canonical title casing for known keys
            for canonical in SKILL_SYNONYMS:
                if normalize_skill(canonical) == norm:
                    display = canonical.title() if canonical.islower() else canonical
                    # Special cases
                    specials = {
                        "javascript": "JavaScript",
                        "typescript": "TypeScript",
                        "postgresql": "PostgreSQL",
                        "mongodb": "MongoDB",
                        "nodejs": "Node.js",
                        "ci/cd": "CI/CD",
                        "html": "HTML",
                        "css": "CSS",
                        "sql": "SQL",
                        "aws": "AWS",
                        "rest api": "REST API",
                        "c++": "C++",
                        "c#": "C#",
                        "machine learning": "Machine Learning",
                        "artificial intelligence": "Artificial Intelligence",
                        "amazon web services": "AWS",
                        "google cloud platform": "GCP",
                        "microsoft azure": "Azure",
                    }
                    display = specials.get(canonical, display)
                    break
            result.append(display)
    return result


def skill_overlap_score(
    cv_skills: Iterable[str],
    required_skills: Iterable[str],
) -> tuple[float, list[str], list[str]]:
    """
    Return (score_0_100, present_skills, missing_skills).
    Score is |intersection| / |required| * 100 when required is non-empty.
    """
    cv_norm = {normalize_skill(s) for s in cv_skills if s}
    required_list = [s for s in required_skills if s]
    required_norm = [normalize_skill(s) for s in required_list]

    if not required_norm:
        present = canonicalize_skills(cv_norm)
        return 100.0, present, []

    present_norm: list[str] = []
    missing_norm: list[str] = []
    seen_present: set[str] = set()
    seen_missing: set[str] = set()

    for original, norm in zip(required_list, required_norm):
        if norm in cv_norm:
            if norm not in seen_present:
                present_norm.append(original)
                seen_present.add(norm)
        else:
            if norm not in seen_missing:
                missing_norm.append(original)
                seen_missing.add(norm)

    unique_required = len(set(required_norm))
    matched = len(seen_present)
    score = (matched / unique_required) * 100.0 if unique_required else 100.0
    return score, canonicalize_skills(present_norm), canonicalize_skills(missing_norm)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", (text or "").lower()))


def score_interview_answer(question: str, answer_tips: str, answer: str) -> int:
    """Score one written answer from 0 to 100 using length and overlap with the expected points."""
    text = (answer or "").strip()
    if len(text) < 8:
        return 0
    answer_tokens = _tokens(text)
    if not answer_tokens:
        return 0
    reference = _tokens(f"{question} {answer_tips}")
    overlap = 0.0
    if reference:
        overlap = len(answer_tokens & reference) / max(1, min(8, len(reference)))
    length_score = min(1.0, len(answer_tokens) / 25)
    raw = 55 * length_score + 45 * min(1.0, overlap)
    return int(round(max(0.0, min(100.0, raw))))


def apply_interview_score(
    breakdown: dict | None,
    interview_score: float,
    weight: float = 0.2,
) -> tuple[int, dict]:
    """Fold an interview score into the skills + semantic breakdown.

    The original contributions stay stored as *_base. A second call uses those
    bases, so submitting again does not shrink the CV score twice.
    """
    updated = dict(breakdown or {})
    skills_base = float(updated.get("skills_contribution_base", updated.get("skills_contribution") or 0))
    semantic_base = float(
        updated.get("semantic_contribution_base", updated.get("semantic_contribution") or 0)
    )
    nice = float(updated.get("nice_to_have_bonus") or 0)
    interview_score = max(0.0, min(100.0, float(interview_score)))
    weight = max(0.0, min(0.5, float(weight)))
    keep = 1.0 - weight
    skills_contrib = skills_base * keep
    semantic_contrib = semantic_base * keep
    interview_contrib = weight * interview_score
    final = int(round(min(100.0, skills_contrib + semantic_contrib + nice + interview_contrib)))
    updated.update(
        {
            "skills_contribution_base": round(skills_base, 1),
            "semantic_contribution_base": round(semantic_base, 1),
            "skills_contribution": round(skills_contrib, 1),
            "semantic_contribution": round(semantic_contrib, 1),
            "interview_score": round(interview_score, 1),
            "interview_weight": weight,
            "interview_contribution": round(interview_contrib, 1),
        }
    )
    return final, updated
