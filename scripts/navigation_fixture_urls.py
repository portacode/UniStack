"""Routes for the disposable navigation browser fixture only."""
from django.urls import path
from django.views.generic import TemplateView
from config.urls import urlpatterns as original_urls

urlpatterns = [
    path(url, TemplateView.as_view(template_name='fixture/page.html', extra_context={
        'page_title': title, 'page_description': 'A customized product with unified navigation.',
        'page_module': 'fixture.js',
    })) for url, title in [
        ('workspace/', 'Workspace'), ('workspace/library/', 'Library'),
        ('workspace/library/new/', 'Add document'), ('materials/42/', 'Document detail'),
        ('preferences/', 'Preferences'), ('reports/', 'Reports'),
    ]
] + original_urls
