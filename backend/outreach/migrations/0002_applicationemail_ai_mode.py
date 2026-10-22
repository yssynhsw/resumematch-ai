from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("outreach", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationemail",
            name="ai_mode",
            field=models.CharField(default="mock", max_length=16),
        ),
    ]
