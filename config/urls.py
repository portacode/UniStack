from django.contrib import admin
from django.urls import include, path
from core.views import protected_media

urlpatterns = [
    path("admin/", admin.site.urls),
    path("unicom/", include("unicom.urls")),
    path("unicrm/", include("unicrm.urls")),
    path("unibot/", include("unibot.urls")),
    path("", include("core.urls")),
    path("media/<path:path>", protected_media),
]
