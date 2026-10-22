from django.contrib import admin

from .models import ApplicationEmail


@admin.register(ApplicationEmail)
class ApplicationEmailAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "analysis", "subject", "used_interview", "created_at")
