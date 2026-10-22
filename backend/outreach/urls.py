from django.urls import path

from .views import ApplicationEmailDetailView, ApplicationEmailListCreateView

urlpatterns = [
    path("", ApplicationEmailListCreateView.as_view(), name="outreach-list"),
    path("<int:pk>/", ApplicationEmailDetailView.as_view(), name="outreach-detail"),
]
