"""Validate the shared shell without prescribing a product's page design."""
from html.parser import HTMLParser
from pathlib import Path
from django.apps import apps
from django.conf import settings
from django.urls import get_resolver

from .navigation import navigation_for


def project_page_paths():
    """Discover static routes from installed project apps, excluding integrations.

    Parameterized detail URLs need product-specific browser tests. Only inspect
    routes owned by applications inside this checkout, not third-party endpoints.
    """
    root = Path(settings.BASE_DIR).resolve()
    local = set()
    for app in apps.get_app_configs():
        location = Path(app.path).resolve()
        if location.is_relative_to(root) and not location.is_relative_to(root / 'apps') and app.name != 'core':
            local.update((app.name, app.label))

    def walk(patterns, prefix='', owned=False):
        for pattern in patterns:
            route = getattr(pattern.pattern, '_route', None)
            if route is None or '<' in route:
                continue
            full = prefix + route
            if hasattr(pattern, 'url_patterns'):
                yield from walk(pattern.url_patterns, full, owned or pattern.app_name in local)
            else:
                callback = getattr(pattern.callback, 'view_class', pattern.callback)
                module = callback.__module__
                if owned or any(module == name or module.startswith(name + '.') for name in local):
                    yield '/' + full

    return set(walk(get_resolver().url_patterns))


class ShellParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.body_classes = []
        self.in_navigation = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "body":
            self.body_classes = attrs.get("class", "").split()
        if tag == "nav" and attrs.get("id") == "site-navigation":
            self.in_navigation = True
        elif tag == "a" and self.in_navigation:
            self.links.append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_navigation = False


def check_shell(response):
    parser = ShellParser()
    parser.feed(response.content.decode(response.charset))
    for element in ("site-navigation", "main-content", "page-skeleton", "navigation-status", "page-label"):
        if parser.ids.count(element) != 1:
            raise ValueError(f"Expected one #{element}; extend core/page.html or core/base.html instead of creating another app shell")
    entries = navigation_for(response.wsgi_request)
    if parser.links != [entry["url"] for entry in entries]:
        raise ValueError("Navigation differs from SITE_NAVIGATION; configure the shared navigation instead of duplicating it")
    expected = "mobile-tabs" if 0 < len(entries) <= 5 else "mobile-menu"
    if expected not in parser.body_classes:
        raise ValueError("Mobile navigation mode differs from the shared shell")
