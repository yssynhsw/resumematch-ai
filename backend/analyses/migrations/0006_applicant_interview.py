import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyses", "0005_interview_attempt"),
        ("cvs", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ApplicantInterview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("questions", models.JSONField(blank=True, default=list)),
                ("answers", models.JSONField(blank=True, default=list)),
                ("question_scores", models.JSONField(blank=True, default=list)),
                ("score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("summary", models.TextField(blank=True, default="")),
                (
                    "state",
                    models.CharField(
                        choices=[("in_progress", "En cours"), ("scored", "Noté")],
                        default="in_progress",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "cv",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applicant_interview",
                        to="cvs.cv",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applicant_interviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
