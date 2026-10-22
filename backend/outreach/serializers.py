from rest_framework import serializers

from .models import ApplicationEmail


class ApplicationEmailSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="analysis.job_offer.title", read_only=True)
    company = serializers.CharField(source="analysis.job_offer.company", read_only=True)

    class Meta:
        model = ApplicationEmail
        fields = (
            "id",
            "analysis",
            "job_title",
            "company",
            "subject",
            "body",
            "skills",
            "used_interview",
            "language",
            "ai_mode",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "analysis",
            "job_title",
            "company",
            "skills",
            "used_interview",
            "language",
            "ai_mode",
            "created_at",
            "updated_at",
        )


class ApplicationEmailCreateSerializer(serializers.Serializer):
    analysis_id = serializers.IntegerField()
    language = serializers.ChoiceField(choices=(("fr", "Français"), ("en", "English")), default="fr")
