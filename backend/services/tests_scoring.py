from django.test import TestCase

from services.scoring import apply_interview_score, normalize_skill, score_interview_answer, skill_overlap_score


class ScoringTests(TestCase):
    def test_synonyms(self):
        self.assertEqual(normalize_skill("JS"), normalize_skill("JavaScript"))
        self.assertEqual(normalize_skill("Postgres"), normalize_skill("PostgreSQL"))
        self.assertEqual(normalize_skill("k8s"), normalize_skill("Kubernetes"))

    def test_overlap_score(self):
        score, present, missing = skill_overlap_score(
            ["Python", "JS", "Git"],
            ["Python", "JavaScript", "Docker"],
        )
        self.assertAlmostEqual(score, 66.7, places=0)
        self.assertIn("Python", present)
        self.assertTrue(any("JavaScript" in p or "javascript" in p.lower() for p in present) or "JS" in str(present))
        self.assertTrue(any("docker" in m.lower() for m in missing))

    def test_interview_answer_and_blend(self):
        self.assertEqual(score_interview_answer("Question", "tips", "short"), 0)
        long_answer = "I shipped a Python Django API with tests and Git for two thousand users " * 3
        self.assertGreater(score_interview_answer("Python Django", "API tests", long_answer), 50)
        breakdown = {"skills_contribution": 40, "semantic_contribution": 30, "nice_to_have_bonus": 2}
        final, updated = apply_interview_score(breakdown, 80, weight=0.2)
        self.assertEqual(updated["skills_contribution_base"], 40)
        self.assertEqual(updated["interview_score"], 80)
        self.assertEqual(final, round(40 * 0.8 + 30 * 0.8 + 2 + 0.2 * 80))
        again, _updated_again = apply_interview_score(updated, 80, weight=0.2)
        self.assertEqual(again, final)
