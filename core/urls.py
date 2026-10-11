from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .auth import signup

urlpatterns = [
    path("", views.home, name="home"),
    path("assistant/", views.assistant, name="assistant"),
    path("accounts/login/", auth_views.LoginView.as_view(extra_context={"page_title": "Sign in"}), name="login"),
    path("accounts/signup/", signup, name="signup"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("health/", views.health, name="health"),
    path("api/ai/respond/", views.ai_respond, name="ai-respond"),
    path("api/ai/retry/", views.retry_failed, name="ai-retry"),
    path("api/ai/usage/", views.usage, name="ai-usage"),
]
