"""The single navigation definition used by every server-rendered page."""
from django.conf import settings


def navigation_for(request):
    entries = []
    best, best_length = None, -1
    for item in settings.SITE_NAVIGATION:
        if item.get("authenticated") and not request.user.is_authenticated:
            continue
        entry = {**item, "active": False}
        entries.append(entry)
        paths = [item["url"], *item.get("match", [])]
        for path in paths:
            matches = request.path == path or (
                not item.get("exact") and path != "/"
                and request.path.startswith(path.rstrip("/") + "/")
            )
            if matches and len(path) > best_length:
                best, best_length = entry, len(path)
    if best is not None:
        best["active"] = True
    return entries
