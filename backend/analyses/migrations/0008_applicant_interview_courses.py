from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyses", "0007_applicant_interview_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicantinterview",
            name="courses",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
