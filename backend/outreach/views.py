from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from analyses.models import Analysis

from .models import ApplicationEmail
from .serializers import ApplicationEmailCreateSerializer, ApplicationEmailSerializer
from .services import create_application_email


class AIThrottle(UserRateThrottle):
    scope = "ai"


class ApplicationEmailListCreateView(APIView):
    def get_throttles(self):
        if self.request.method == "POST":
            return [AIThrottle()]
        return super().get_throttles()

    def get(self, request):
        qs = ApplicationEmail.objects.filter(user=request.user).select_related("analysis__job_offer")
        analysis_id = request.query_params.get("analysis")
        if analysis_id:
            qs = qs.filter(analysis_id=analysis_id)
        return Response(ApplicationEmailSerializer(qs[:20], many=True).data)

    def post(self, request):
        serializer = ApplicationEmailCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analysis = get_object_or_404(
            Analysis.objects.select_related("cv", "job_offer", "user"),
            pk=serializer.validated_data["analysis_id"],
            user=request.user,
        )
        email = create_application_email(analysis, serializer.validated_data["language"])
        return Response(ApplicationEmailSerializer(email).data, status=status.HTTP_201_CREATED)


class ApplicationEmailDetailView(APIView):
    def get_object(self, request, pk):
        return get_object_or_404(
            ApplicationEmail.objects.select_related("analysis__job_offer"),
            pk=pk,
            user=request.user,
        )

    def put(self, request, pk):
        email = self.get_object(request, pk)
        serializer = ApplicationEmailSerializer(email, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationEmailSerializer(email).data)
