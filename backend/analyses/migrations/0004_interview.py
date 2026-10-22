import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyses", "0003_job_search"),
    ]

    operations = [
        migrations.CreateModel(
            name="Interview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("held_on", models.DateField()),
                (
                    "format",
                    models.CharField(
                        choices=[("phone", "Téléphone"), ("video", "Visioconférence"), ("onsite", "Sur site")],
                        default="video",
                        max_length=10,
                    ),
                ),
                ("questions", models.TextField(blank=True, default="")),
                ("feedback", models.TextField(blank=True, default="")),
                (
                    "outcome",
                    models.CharField(
                        choices=[("pending", "En attente"), ("passed", "Retenu"), ("rejected", "Refusé")],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "analysis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="interviews",
                        to="analyses.analysis",
                    ),
                ),
            ],
            options={
                "ordering": ["held_on", "id"],
            },
        ),
    ]
