"""Isolated browser fixture: DJANGO_SETTINGS_MODULE=scripts.navigation_fixture.

Use only with a disposable database; never deploy this settings module publicly.
"""
from config.settings import *  # noqa: F403

ROOT_URLCONF = 'scripts.navigation_fixture_urls'
SITE_NAVIGATION = [
    {"label": "Workspace", "url": "/workspace/", "exact": True, "icon": "overview"},
    {"label": "Document library", "mobile_label": "Library", "url": "/workspace/library/", "match": ["/materials/"], "icon": "documents"},
    {"label": "Add document", "mobile_label": "Add", "url": "/workspace/library/new/", "icon": "upload"},
    {"label": "Preferences", "mobile_label": "Settings", "url": "/preferences/", "icon": "settings"},
    {"label": "Assistant", "mobile_label": "Chat", "url": "/assistant/", "icon": "assistant"},
]
if os.environ.get("NAV_FIXTURE_COUNT") == "6":  # noqa: F405
    SITE_NAVIGATION.append({"label": "Reports", "url": "/reports/", "icon": "documents"})
SITE_STYLESHEETS = ['fixture.css']
STATICFILES_DIRS = [BASE_DIR / 'scripts/fixtures/navigation']  # noqa: F405
TEMPLATES[0]['APP_DIRS'] = False  # noqa: F405
TEMPLATES[0]['OPTIONS']['loaders'] = [  # noqa: F405
    ('django.template.loaders.locmem.Loader', {
        'fixture/page.html': """{% extends 'core/page.html' %}
{% block page_actions %}<a class="button primary" href="/workspace/library/new/" data-nav>Add document</a>{% endblock %}
{% block page_content %}<div class="fixture-content"><p>This product page uses the shared shell.</p><button id="fixture-action" class="button secondary">Local page action</button><output id="fixture-count">0</output><a href="/materials/42/" data-nav>Open detail</a></div>{% endblock %}""",
    }),
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]
