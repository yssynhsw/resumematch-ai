import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyses", "0006_applicant_interview"),
    ]

    operations = [
        migrations.AlterField(
            model_name="applicantinterview",
            name="cv",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="applicant_interviews",
                to="cvs.cv",
            ),
        ),
        migrations.AddField(
            model_name="applicantinterview",
            name="kind",
            field=models.CharField(
                choices=[("technical", "Technical"), ("soft", "Soft")],
                default="technical",
                max_length=20,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="applicantinterview",
            unique_together={("cv", "kind")},
        ),
    ]
