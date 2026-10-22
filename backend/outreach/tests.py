from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import User
from analyses.models import Analysis, InterviewAttempt, JobOffer
from cvs.models import CV
from rest_framework.test import APIClient

from .models import ApplicationEmail


@override_settings(LLM_API_KEY="", DEEPSEEK_API_KEY="")
class ApplicationEmailTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="karim", password="pass12345!", first_name="Karim")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.cv = CV.objects.create(
            user=self.user,
            file=SimpleUploadedFile("cv.pdf", b"%PDF-1.4"),
            original_filename="cv.pdf",
            extracted_text="Développeur React, TypeScript, Git et API REST.",
            parsed_data={"technical_skills": ["React", "TypeScript", "Git"]},
        )
        self.offer = JobOffer.objects.create(
            user=self.user,
            title="Développeur Frontend React",
            company="Swile",
            raw_text="React TypeScript",
        )
        self.analysis = Analysis.objects.create(
            user=self.user,
            cv=self.cv,
            job_offer=self.offer,
            score=78,
            present_skills=["React"],
            status=Analysis.Status.INTERVIEW,
        )
        InterviewAttempt.objects.create(
            analysis=self.analysis,
            state=InterviewAttempt.State.SCORED,
            questions=[{"question": "Why this company?"}],
            answers=["I built a React design system used by the product team."],
            score=51,
        )

    def test_email_uses_skills_interview_and_application(self):
        res = self.client.post(
            "/api/outreach/",
            {"analysis_id": self.analysis.id, "language": "en"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        body = res.data["body"]
        self.assertEqual(res.data["subject"], "Application for Développeur Frontend React")
        self.assertTrue(body.startswith("Dear Hiring Manager,"))
        self.assertIn("I am writing to express my interest", body)
        self.assertIn("Swile", body)
        self.assertIn("React", body)
        self.assertIn("React design system", body)
        self.assertIn("I would welcome the opportunity", body)
        self.assertIn("Thank you for your time and consideration.", body)
        self.assertIn("Best regards,\nKarim", body)
        self.assertGreaterEqual(len(body.split()), 100)
        self.assertLessEqual(len(body.split()), 180)
        self.assertTrue(res.data["used_interview"])
        self.assertEqual(res.data["skills"][:1], ["React"])
        self.assertEqual(ApplicationEmail.objects.filter(user=self.user).count(), 1)

        listed = self.client.get(f"/api/outreach/?analysis={self.analysis.id}")
        self.assertEqual(len(listed.data), 1)

        other = APIClient()
        other.force_authenticate(User.objects.create_user(username="lea", password="pass12345!"))
        self.assertEqual(other.get("/api/outreach/").data, [])
