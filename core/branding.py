"""One project-owned brand shared by the website, authentication and chat."""
import json
import re
from pathlib import Path

from django.conf import settings


def luminance(color):
    values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))


def contrast_text(color):
    light = luminance(color)
    dark_contrast = (light + .05) / (luminance("#111827") + .05)
    return "#111827" if dark_contrast >= 4.5 else "#ffffff"


def action_color(color):
    # Upstream controls use white icons; darken pale brands without patching
    # the shared component. Other brand surfaces retain the exact input color.
    while luminance(color) > .16:
        color = '#' + ''.join(f'{int(int(color[i:i + 2], 16) * .9):02x}' for i in (1, 3, 5))
    return color


def get_brand():
    path = Path(settings.BASE_DIR) / "branding.json"
    data = json.loads(path.read_text()) if path.exists() else {}
    brand = {"name": "Workspace", "tagline": "A place to get things done.",
             "primary": "#3157d5", "accent": "#0f766e", "logo": ""}
    brand.update({key: str(data[key]) for key in brand if key in data})
    for key in ("primary", "accent"):
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", brand[key]):
            raise ValueError(f"Brand {key} must be a six-digit hex color")
        brand[key + "_text"] = contrast_text(brand[key])
    # Only deployment-generated local raster assets are rendered as a logo.
    if brand["logo"] and not re.fullmatch(r"core/brand/logo\.(png|jpg|webp)", brand["logo"]):
        raise ValueError("Brand logo must be a local core/brand raster asset")
    brand["initial"] = brand["name"][:1].upper()
    brand["action"] = action_color(brand["primary"])
    return brand


def context(request):
    navigation = []
    for item in settings.SITE_NAVIGATION:
        if item.get("authenticated") and not request.user.is_authenticated:
            continue
        entry = dict(item)
        entry["active"] = request.path == item["url"] or (
            item["url"] != "/" and request.path.startswith(item["url"].rstrip("/") + "/")
        )
        navigation.append(entry)
    return {"brand": get_brand(), "site_navigation": navigation,
            "mobile_bottom_nav": 0 < len(navigation) <= 5,
            "signup_enabled": settings.UNISTACK_ALLOW_SIGNUP,
            "guest_chat_enabled": settings.UNISTACK_ALLOW_ANONYMOUS_CHAT}
