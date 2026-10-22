"""Draft an application email from CV skills, the interview, and the application."""

from __future__ import annotations

import re

from pydantic import BaseModel

from analyses.models import Analysis, ApplicantInterview, InterviewAttempt
from services.ai_service import get_ai_service

from .models import ApplicationEmail


class EmailDraft(BaseModel):
    subject: str = ""
    body: str = ""

    def normalized(self) -> "EmailDraft":
        subject = (self.subject or "").strip()
        body = (self.body or "").strip()
        return EmailDraft(subject=subject[:200], body=body)


def _skills(analysis: Analysis) -> list[str]:
    parsed = analysis.cv.parsed_data or {}
    skills = list(parsed.get("technical_skills") or []) + list(parsed.get("soft_skills") or [])
    if not skills:
        skills = list(analysis.present_skills or [])
    cleaned = []
    seen = set()
    for skill in skills:
        text = str(skill or "").strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            cleaned.append(text)
    return cleaned[:12]


def _lines_from(questions: list, answers: list) -> list[str]:
    lines = []
    for index, question in enumerate(questions):
        answer = answers[index] if index < len(answers) else ""
        if not str(answer or "").strip():
            continue
        category = question.get("category") or ""
        lines.append(f"[{category}] Q: {question.get('question', '')}\nA: {answer}")
    return lines[:8]


def _interview_lines(analysis: Analysis) -> list[str]:
    """Prefer the CV evaluation. It is independent from the job application."""
    scored = [
        interview
        for interview in analysis.cv.applicant_interviews.all()
        if interview.state == ApplicantInterview.State.SCORED
    ]
    if scored:
        lines: list[str] = []
        for interview in scored:
            lines.extend(_lines_from(list(interview.questions or []), list(interview.answers or [])))
        return lines
    try:
        attempt = analysis.interview_attempt
    except InterviewAttempt.DoesNotExist:
        return []
    if attempt.state != InterviewAttempt.State.SCORED:
        return []
    return _lines_from(list(attempt.questions or []), list(attempt.answers or []))


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _clip_words(text: str, limit: int) -> str:
    words = text.split()
    cleaned = text.strip()
    if len(words) <= limit:
        return cleaned
    clipped = " ".join(words[:limit])
    for mark in (".", "!", "?"):
        cut = clipped.rfind(mark)
        if cut >= 40:
            return clipped[: cut + 1].strip()
    return clipped.rstrip(".,;:") + "."


def _recipient_name(analysis: Analysis) -> str:
    parsed = analysis.job_offer.parsed_data or {}
    for key in ("recipient_name", "contact_name", "hiring_manager", "recruiter"):
        value = str(parsed.get(key) or "").strip()
        if value:
            return value[:80]
    return ""


def _grouped_answers(interview_lines: list[str]) -> tuple[str, str, str]:
    environment = ""
    soft_personal = ""
    soft_other = ""
    other = ""
    for line in interview_lines:
        answer = line.split("A:", 1)[-1].strip()
        if not answer:
            continue
        marker = line.lower()
        if "[environnement]" in marker or "environnement de travail" in marker or "work environment" in marker:
            environment = environment or answer
        elif "soft skill" in marker:
            soft_personal = soft_personal or answer
        elif "[comportementale]" in marker:
            soft_other = soft_other or answer
        else:
            other = other or answer
    soft = soft_personal or soft_other
    if soft == other:
        soft = ""
    if environment in (other, soft):
        environment = ""
    return environment, soft, other


def _mock_email(analysis: Analysis, skills: list[str], interview_lines: list[str], language: str) -> EmailDraft:
    """Purpose, context, request, thanks, then the signature. About 100–180 words."""
    name = (analysis.user.get_full_name() or analysis.user.username).strip() or "Candidate"
    title = analysis.job_offer.title or ("the open role" if language == "en" else "le poste")
    company = analysis.job_offer.company or ("your organisation" if language == "en" else "votre entreprise")
    skill_text = ", ".join(skills[:4]) or ("my current experience" if language == "en" else "mon expérience actuelle")
    recipient = _recipient_name(analysis)
    environment, soft, other = _grouped_answers(interview_lines)
    en = language == "en"
    subject = f"Application for {title}" if en else f"Candidature au poste de {title}"
    quote_limit = 28
    while True:
        if en:
            greeting = f"Dear {recipient}," if recipient else "Dear Hiring Manager,"
            purpose = f"I am writing to express my interest in the {title} position at {company}."
            context = (
                f"I am applying on the basis of my CV, which shows practical work with {skill_text}. "
                "These skills are the ones I would use in this role, and they are the reason this application is a fit. "
                "I am motivated by work that stays close to that experience, inside a team where the way of working is clear."
            )
            if other:
                context += f" In the interview I explained the following: {_clip_words(other, quote_limit)}"
            if environment:
                context += f" On the work environment that suits me, I said: {_clip_words(environment, quote_limit)}"
            if soft:
                context += f" On the soft skill I use most with a team, I said: {_clip_words(soft, quote_limit)}"
            context += " This is the context I would like you to consider with the CV."
            request = "I would welcome the opportunity to discuss this application further."
            thanks = "Thank you for your time and consideration."
            closing = f"Best regards,\n{name}"
        else:
            greeting = f"Cher {recipient}," if recipient else "Madame, Monsieur,"
            purpose = f"Je vous écris afin de vous faire part de mon intérêt pour le poste de {title} au sein de {company}."
            context = (
                f"Je me fonde sur mon CV, qui montre une pratique concrète de {skill_text}. "
                "Ce sont les compétences que j'utiliserais dans ce poste, et elles expliquent l'adéquation de ma candidature. "
                "Je souhaite un travail proche de cette expérience, dans une équipe où la façon de travailler est claire."
            )
            if other:
                context += f" Lors de l'entretien, j'ai précisé : {_clip_words(other, quote_limit)}"
            if environment:
                context += f" Sur l'environnement de travail qui me convient, j'ai dit : {_clip_words(environment, quote_limit)}"
            if soft:
                context += f" Sur le soft skill que j'utilise le plus en équipe, j'ai dit : {_clip_words(soft, quote_limit)}"
            context += " C'est le contexte que je souhaite vous soumettre avec le CV."
            request = "Je serais heureux d'avoir l'occasion d'en discuter plus en détail."
            thanks = "Je vous remercie du temps et de l'attention que vous accorderez à ma candidature."
            closing = f"Cordialement,\n{name}"
        body = "\n\n".join([greeting, purpose, context, request, thanks, closing])
        count = _word_count(body)
        if count > 180 and quote_limit > 8:
            quote_limit -= 6
            continue
        return EmailDraft(subject=subject[:200], body=body)


def create_application_email(analysis: Analysis, language: str = "fr") -> ApplicationEmail:
    skills = _skills(analysis)
    interview_lines = _interview_lines(analysis)
    name = (analysis.user.get_full_name() or analysis.user.username).strip()
    title = analysis.job_offer.title
    company = analysis.job_offer.company
    status = analysis.status
    en = language == "en"
    recipient = _recipient_name(analysis) or ("Hiring Manager" if en else "")
    prompt = (
        "Rédige un e-mail de candidature professionnel, un seul objectif : postuler. "
        "100 à 180 mots. Pas de langage familier, pas d'abréviation, pas d'emoji. "
        "N'invente aucune expérience ni aucun nom. "
        "Structure obligatoire, dans cet ordre, et uniquement dans la langue demandée : "
        + (
            "1) subject : « Application for [poste] ». "
            "2) formule d'appel : « Dear [nom], » si un destinataire est connu, sinon « Dear Hiring Manager, ». "
            "3) première phrase : « I am writing to express my interest in... ». "
            "4) contexte utile : compétences réelles du CV, puis, s'ils existent, les propos de l'entretien. "
            "5) une demande claire : « I would welcome the opportunity to discuss this further. ». "
            "6) remerciement : « Thank you for your time and consideration. » puis « Best regards, » "
            "suivi du nom complet. "
            if en
            else
            "1) subject : « Candidature au poste de [poste] ». "
            "2) formule d'appel : « Cher [nom], » si un destinataire est connu, sinon « Madame, Monsieur, ». "
            "3) première phrase : pourquoi la personne écrit. "
            "4) contexte utile : compétences réelles du CV, puis, s'ils existent, les propos de l'entretien. "
            "5) une demande claire : proposer d'en discuter. "
            "6) remerciement puis « Cordialement, » suivi du nom complet. "
        )
        + "Réponds UNIQUEMENT en JSON strict avec les clés subject et body.\n"
        f"Destinataire connu: {recipient or 'inconnu'}.\n"
        f"Langue: {'anglais' if en else 'français'}.\n"
        f"Candidat: {name}\n"
        f"Poste: {title}\n"
        f"Entreprise: {company}\n"
        f"Statut de candidature: {status}\n"
        f"Score de compatibilité: {analysis.score}\n"
        f"Compétences du CV: {', '.join(skills) or 'non extraites'}\n\n"
        f"Entretien:\n" + ("\n\n".join(interview_lines) or "Aucun entretien noté.") + "\n\n"
        f"CV:\n{(analysis.cv.extracted_text or '')[:3000]}"
    )
    ai = get_ai_service()
    draft = ai.run_prompt(
        prompt,
        EmailDraft,
        mock_fn=lambda: _mock_email(analysis, skills, interview_lines, language),
        cache_kind="application_email",
    )
    if not isinstance(draft, EmailDraft):
        draft = EmailDraft.model_validate(draft)
    draft = draft.normalized()
    if not draft.subject:
        draft = _mock_email(analysis, skills, interview_lines, language)
    return ApplicationEmail.objects.create(
        user=analysis.user,
        analysis=analysis,
        subject=draft.subject,
        body=draft.body,
        skills=skills,
        used_interview=bool(interview_lines),
        language=language if language in ("fr", "en") else "fr",
        ai_mode="gemini" if (ai.live_calls or ai.cache_hits) else "mock",
    )
