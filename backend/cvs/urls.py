from django.urls import path

from analyses.views import ApplicantInterviewSubmitView, ApplicantInterviewView

from .views import CVDetailView, CVListCreateView

urlpatterns = [
    path("", CVListCreateView.as_view(), name="cv-list-create"),
    path("<int:pk>/interview/submit", ApplicantInterviewSubmitView.as_view(), name="applicant-interview-submit"),
    path("<int:pk>/interview", ApplicantInterviewView.as_view(), name="applicant-interview"),
    path("<int:pk>/", CVDetailView.as_view(), name="cv-detail"),
]
