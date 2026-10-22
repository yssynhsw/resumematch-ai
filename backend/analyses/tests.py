import shutil
import tempfile
from unittest import mock

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from cvs.models import CV

from .models import Analysis, AnalysisJob, ApplicantInterview, Interview, InterviewAttempt

CV_TEXT = """Jean Dupont
jean.dupont@example.com · +33 6 12 34 56 78
Expérience
Développement d'une API REST en Python et Django pour 2000 utilisateurs
Mise en place de tests automatisés et intégration continue avec Git
Formation
Master Informatique
Compétences
Python, Django, SQL, Git, React
""" + "Projet de fin d'études sur la recommandation de contenus. " * 10

JOB_TEXT = (
    "Poste: Développeur Backend\nEntreprise: Acme\n"
    "Nous recherchons un développeur Python Django avec Docker, SQL et Kubernetes."
)


TEST_MEDIA = tempfile.mkdtemp(prefix="rm-test-media-")


@override_settings(
    LLM_API_KEY="", ANALYSIS_JOBS_SYNC=True, ANALYSIS_DAILY_QUOTA=20, MEDIA_ROOT=TEST_MEDIA
)
class AnalysisApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="alice", password="pass12345!")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.cv = CV.objects.create(
            user=self.user,
            file=SimpleUploadedFile("cv.pdf", b"%PDF-1.4 fake"),
            original_filename="cv.pdf",
            extracted_text=CV_TEXT,
        )

    def _create(self, **extra):
        payload = {"cv_id": self.cv.id, "job_offer_text": JOB_TEXT, "level": "junior", **extra}
        return self.client.post("/api/analyses/", payload, format="json")

    def test_create_analysis_records_mock_mode_and_language(self):
        res = self._create(language="en")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["ai_mode"], "mock")
        self.assertEqual(res.data["language"], "en")
        self.assertIn("Docker", res.data["competences_manquantes"])

    def test_async_job_completes_and_exposes_analysis(self):
        res = self.client.post(
            "/api/analyses/async",
            {"cv_id": self.cv.id, "job_offer_text": JOB_TEXT},
            format="json",
        )
        self.assertEqual(res.status_code, 202)
        job = self.client.get(f"/api/analysis-jobs/{res.data['id']}/").data
        self.assertEqual(job["state"], AnalysisJob.State.DONE)
        self.assertEqual(job["progress"], 100)
        self.assertIsNotNone(job["analysis_id"])

    def test_compare_creates_one_job_per_offer(self):
        res = self.client.post(
            "/api/analyses/compare",
            {
                "cv_id": self.cv.id,
                "offers": [
                    {"job_offer_text": JOB_TEXT, "title": "A"},
                    {"job_offer_text": JOB_TEXT + " React TypeScript", "title": "B"},
                ],
            },
            format="json",
        )
        self.assertEqual(res.status_code, 202)
        self.assertEqual(len(res.data["jobs"]), 2)
        self.assertEqual(Analysis.objects.filter(user=self.user).count(), 2)

    @override_settings(ANALYSIS_DAILY_QUOTA=1)
    def test_daily_quota_blocks_extra_analyses(self):
        self.assertEqual(self._create().status_code, 201)
        res = self._create()
        self.assertEqual(res.status_code, 429)

    def test_extras_are_generated_then_cached(self):
        analysis_id = self._create().data["id"]
        for kind in ("interview_prep", "cv_rewrite", "learning_plan", "ats"):
            empty = self.client.get(f"/api/analyses/{analysis_id}/extras/{kind}?language=fr")
            self.assertIsNone(empty.data["data"])
            res = self.client.post(
                f"/api/analyses/{analysis_id}/extras/{kind}", {"language": "fr"}, format="json"
            )
            self.assertEqual(res.status_code, 200, kind)
            self.assertTrue(res.data["data"], kind)
            cached = self.client.get(f"/api/analyses/{analysis_id}/extras/{kind}?language=fr")
            self.assertEqual(cached.data["data"], res.data["data"])

        interview = Analysis.objects.get(pk=analysis_id).extras["interview_prep:fr"]
        self.assertTrue(any(q["category"] == "lacune" for q in interview["questions"]))

    def test_unknown_extra_kind_is_404(self):
        analysis_id = self._create().data["id"]
        res = self.client.post(f"/api/analyses/{analysis_id}/extras/nope", {}, format="json")
        self.assertEqual(res.status_code, 404)

    def test_report_export_is_docx(self):
        analysis_id = self._create().data["id"]
        res = self.client.get(f"/api/analyses/{analysis_id}/report?language=fr")
        self.assertEqual(res.status_code, 200)
        self.assertIn("wordprocessingml", res["Content-Type"])
        self.assertTrue(res.content.startswith(b"PK"))

    def test_dashboard_timeline_is_chronological(self):
        self._create()
        self._create()
        timeline = self.client.get("/api/dashboard/stats/").data["timeline"]
        self.assertEqual(len(timeline), 2)
        self.assertLessEqual(timeline[0]["date"], timeline[1]["date"])

    def test_system_status_reports_mock_mode(self):
        res = APIClient().get("/api/system/status/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["llm_mode"], "mock")

    def test_interview_log_crud_does_not_change_status(self):
        analysis_id = self._create().data["id"]
        created = self.client.post(
            f"/api/analyses/{analysis_id}/interviews",
            {
                "held_on": "2026-11-02",
                "format": "video",
                "questions": "Parlez d'un projet Django.",
                "feedback": "",
                "outcome": "pending",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        interview_id = created.data["id"]
        later = self.client.post(
            f"/api/analyses/{analysis_id}/interviews",
            {"held_on": "2026-10-20", "format": "phone"},
            format="json",
        )
        self.assertEqual(later.status_code, 201)

        listed = self.client.get(f"/api/analyses/{analysis_id}/interviews")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual([item["held_on"] for item in listed.data], ["2026-10-20", "2026-11-02"])

        board = self.client.get("/api/analyses/?page_size=10")
        match = next(item for item in board.data["results"] if item["id"] == analysis_id)
        self.assertEqual(match["next_interview_on"], "2026-10-20")
        self.assertEqual(match["status"], Analysis.Status.TO_APPLY)

        patched = self.client.patch(
            f"/api/analyses/{analysis_id}/interviews/{interview_id}",
            {"outcome": "passed", "feedback": "Bon échange."},
            format="json",
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(patched.data["outcome"], "passed")
        self.assertEqual(Analysis.objects.get(pk=analysis_id).status, Analysis.Status.TO_APPLY)
        self.assertEqual(
            self.client.get(f"/api/analyses/{analysis_id}/").data["next_interview_on"],
            "2026-10-20",
        )

        self.assertEqual(
            self.client.delete(f"/api/analyses/{analysis_id}/interviews/{later.data['id']}").status_code,
            204,
        )
        self.assertEqual(Interview.objects.filter(analysis_id=analysis_id).count(), 1)

        other = APIClient()
        other.force_authenticate(User.objects.create_user(username="bob", password="pass12345!"))
        self.assertEqual(
            other.get(f"/api/analyses/{analysis_id}/interviews").status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/api/analyses/{analysis_id}/interviews",
                {"held_on": "2026-11-02", "format": "carrier"},
                format="json",
            ).status_code,
            400,
        )

    def test_in_app_interview_updates_match_score(self):
        created = self._create()
        analysis_id = created.data["id"]
        before = created.data["score"]
        started = self.client.post(
            f"/api/analyses/{analysis_id}/interview",
            {"language": "fr"},
            format="json",
        )
        self.assertEqual(started.status_code, 200)
        questions = started.data["attempt"]["questions"]
        self.assertGreaterEqual(len(questions), 4)
        self.assertIn("environnement", [item["category"] for item in questions])
        self.assertNotIn("answer_tips", questions[0])
        answer = (
            "J'ai développé une API REST en Python et Django, avec des tests et Git, "
            "pour environ 2000 utilisateurs."
        )
        submitted = self.client.post(
            f"/api/analyses/{analysis_id}/interview/submit",
            {"answers": [answer] * len(questions)},
            format="json",
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertEqual(submitted.data["attempt"]["state"], "scored")
        self.assertGreater(submitted.data["attempt"]["score"], 0)
        self.assertIn("interview_contribution", submitted.data["score_breakdown"])
        self.assertIn("answer_tips", submitted.data["attempt"]["questions"][0])
        self.assertNotEqual(submitted.data["score"], before)

    def test_extend_reopens_scored_interview_with_personal_questions(self):
        created = self._create()
        analysis = Analysis.objects.get(pk=created.data["id"])
        InterviewAttempt.objects.create(
            analysis=analysis,
            state=InterviewAttempt.State.SCORED,
            questions=[{"question": "Parlez de React.", "category": "technique"}],
            answers=["J'ai construit une interface React avec TypeScript."],
            question_scores=[{"index": 0, "score": 60}],
            score=60,
            summary="ok",
        )
        extended = self.client.post(
            f"/api/analyses/{analysis.id}/interview",
            {"language": "fr", "extend": True},
            format="json",
        )
        self.assertEqual(extended.status_code, 200)
        attempt = extended.data["attempt"]
        self.assertEqual(attempt["state"], "in_progress")
        self.assertEqual(attempt["answers"][0], "J'ai construit une interface React avec TypeScript.")
        self.assertEqual(attempt["answers"][-2:], ["", ""])
        self.assertEqual(attempt["questions"][-2]["category"], "environnement")
        self.assertIn("soft skill", attempt["questions"][-1]["question"].lower())

    def test_applicant_interview_does_not_touch_applications(self):
        self.cv.parsed_data = {
            "technical_skills": ["Python", "Django"],
            "soft_skills": ["Teamwork"],
        }
        self.cv.save()
        started = self.client.post(
            f"/api/cvs/{self.cv.id}/interview",
            {"language": "en", "kind": "technical"},
            format="json",
        )
        self.assertEqual(started.status_code, 200)
        questions = started.data["attempt"]["questions"]
        self.assertEqual(len(questions), 2)
        self.assertEqual(started.data["attempt"]["courses"], [])
        technical_text = " ".join(item["question"] for item in questions)
        self.assertIn("Python", technical_text)
        self.assertIn("Django", technical_text)
        self.assertTrue(all(item["category"] == "technique" for item in questions))
        soft = self.client.post(
            f"/api/cvs/{self.cv.id}/interview",
            {"language": "en", "kind": "soft"},
            format="json",
        )
        self.assertEqual(soft.status_code, 200)
        soft_questions = soft.data["attempt"]["questions"]
        self.assertEqual(len(soft_questions), 1)
        self.assertIn("Teamwork", soft_questions[0]["question"])
        self.assertEqual(soft.data["attempt"]["courses"], [])
        self.assertEqual(Analysis.objects.count(), 0)
        answer = "I built a Django API with tests and Git for about 2000 users, as written on my CV."
        submitted = self.client.post(
            f"/api/cvs/{self.cv.id}/interview/submit",
            {"answers": [answer] * len(questions), "kind": "technical"},
            format="json",
        )
        self.assertEqual(submitted.status_code, 200)
        self.assertGreater(submitted.data["attempt"]["score"], 0)
        self.assertNotIn("score_breakdown", submitted.data)
        courses = submitted.data["attempt"]["courses"]
        self.assertTrue(courses)
        course_skills = {item["skill"] for item in courses}
        self.assertIn("Python", course_skills)
        self.assertIn("Django", course_skills)
        for course in courses:
            self.assertTrue(course["title"])
            self.assertTrue(str(course["url"]).startswith("https://"))
            self.assertTrue(course["reason"])
        soft_row = ApplicantInterview.objects.get(cv=self.cv, kind=ApplicantInterview.Kind.SOFT)
        self.assertEqual(soft_row.courses, [])
        self.assertEqual(Analysis.objects.count(), 0)
        self.user.refresh_from_db()
        self.assertEqual(self.user.score, submitted.data["attempt"]["score"])
        self.assertEqual(submitted.data["user_score"], self.user.score)
        again = self.client.post(
            f"/api/cvs/{self.cv.id}/interview/submit",
            {"answers": [answer] * len(questions), "kind": "technical"},
            format="json",
        )
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.data["attempt"]["score"], submitted.data["attempt"]["score"])
        self.user.refresh_from_db()
        self.assertEqual(self.user.score, again.data["attempt"]["score"])
        self.assertEqual(again.data["user_score"], self.user.score)
        self.assertEqual(ApplicantInterview.objects.filter(cv=self.cv).count(), 2)
        self.assertEqual(
            set(ApplicantInterview.objects.filter(cv=self.cv).values_list("kind", flat=True)),
            {"technical", "soft"},
        )
        self.assertNotEqual(started.data["attempt"]["id"], soft.data["attempt"]["id"])
        technical = ApplicantInterview.objects.get(cv=self.cv, kind=ApplicantInterview.Kind.TECHNICAL)
        technical.courses = []
        technical.save(update_fields=["courses"])
        reloaded = self.client.post(
            f"/api/cvs/{self.cv.id}/interview",
            {"language": "en", "kind": "technical"},
            format="json",
        )
        self.assertEqual(reloaded.status_code, 200)
        self.assertEqual(reloaded.data["attempt"]["state"], "scored")
        reloaded_skills = {item["skill"] for item in reloaded.data["attempt"]["courses"]}
        self.assertIn("Python", reloaded_skills)
        self.assertIn("Django", reloaded_skills)
        soft_row.refresh_from_db()
        self.assertEqual(soft_row.courses, [])

    def test_other_users_cannot_read_jobs_or_extras(self):
        analysis_id = self._create().data["id"]
        other = APIClient()
        other.force_authenticate(User.objects.create_user(username="bob", password="pass12345!"))
        res = other.post(f"/api/analyses/{analysis_id}/extras/ats", {}, format="json")
        self.assertEqual(res.status_code, 404)

    @mock.patch("analyses.views.import_job_offer")
    def test_import_url_endpoint(self, import_mock):
        import_mock.return_value = {"title": "Dev", "company": "Acme", "text": "x" * 200, "source": "json-ld"}
        res = self.client.post(
            "/api/job-offers/import-url", {"url": "https://jobs.example.com/1"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["company"], "Acme")
