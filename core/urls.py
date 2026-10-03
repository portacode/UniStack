from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("api/ai/respond/", views.ai_respond, name="ai-respond"),
    path("api/ai/retry/", views.retry_failed, name="ai-retry"),
    path("api/ai/usage/", views.usage, name="ai-usage"),
]
