from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("unicom/", include("unicom.urls")),
    path("unicrm/", include("unicrm.urls")),
    path("unibot/", include("unibot.urls")),
    path("", include("core.urls")),
    path("media/<path:path>", login_required(serve, login_url="/admin/login/"), {"document_root": settings.MEDIA_ROOT}),
]
